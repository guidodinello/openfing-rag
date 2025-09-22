import asyncio
import hashlib
from typing import Any

from cachetools import TTLCache

from shared.database.models import MessageRole
from shared.logging import get_logger

logger = get_logger(__name__)

ONE_HOUR = 3600


class EphemeralConversationHandler:
    """
    Thread-safe and async-safe handler for ephemeral (anonymous) conversations.
    Uses asyncio locks to prevent race conditions in async contexts.
    """

    def __init__(self, max_sessions: int = 1000, ttl_seconds: int = ONE_HOUR, max_history_length: int = 20):
        """
        Initialize the ephemeral conversation handler.

        Args:
            max_sessions: Maximum number of concurrent sessions to cache
            ttl_seconds: Time-to-live for sessions in seconds (default: 1 hour)
            max_history_length: Maximum number of messages to keep per session
        """
        self._session_cache: TTLCache = TTLCache(maxsize=max_sessions, ttl=ttl_seconds)
        self._cache_lock = asyncio.Lock()
        self._max_history_length = max_history_length

        logger.info(
            f"EphemeralConversationHandler initialized: "
            f"max_sessions={max_sessions}, ttl={ttl_seconds}s, max_history={max_history_length}",
        )

    async def get_session_history(self, session_id: str) -> list[dict[str, Any]]:
        """
        Get conversation history from session cache.
        Returns a copy to prevent external mutations.

        Args:
            session_id: Unique session identifier

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        async with self._cache_lock:
            history = self._session_cache.get(session_id, [])
            # Return a deep copy to prevent mutations affecting cached data
            return [msg.copy() for msg in history]

    async def update_session_history(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """
        Update session cache with new messages.
        Fetches fresh history from cache to prevent race conditions.

        Args:
            session_id: Unique session identifier
            user_message: User's message content
            assistant_message: Assistant's response content
            existing_history: Optional existing history (ignored, fetched fresh from cache)
        """
        async with self._cache_lock:
            # Always fetch fresh history from cache to avoid race conditions
            current_history = self._session_cache.get(session_id, [])

            # Append new messages
            current_history.extend(
                [
                    {"role": MessageRole.USER, "content": user_message},
                    {"role": MessageRole.ASSISTANT, "content": assistant_message},
                ],
            )

            # Trim to max length, keeping most recent messages
            trimmed_history = current_history[-self._max_history_length :]

            # Update cache
            self._session_cache[session_id] = trimmed_history

            logger.debug(
                f"Updated session {session_id}: "
                f"{len(current_history)} -> {len(trimmed_history)} messages "
                f"(trimmed: {len(current_history) > self._max_history_length})",
            )

    def generate_anonymous_message_id(self, user_msg: str, assistant_msg: str) -> int:
        """
        Generate a consistent ID for anonymous messages.
        Uses MD5 hash for deterministic ID generation.

        Args:
            user_msg: User's message content
            assistant_msg: Assistant's response content

        Returns:
            Integer ID based on message content hash
        """
        content = f"{user_msg}_{assistant_msg}"
        hash_digest = hashlib.md5(content.encode()).hexdigest()
        # Convert first 8 hex chars to int
        return int(hash_digest[:8], 16)

    async def clear_session_history(self, session_id: str) -> bool:
        """
        Clear session history for a specific session.

        Args:
            session_id: Unique session identifier

        Returns:
            True if session existed and was cleared, False otherwise
        """
        async with self._cache_lock:
            if session_id in self._session_cache:
                del self._session_cache[session_id]
                logger.info(f"Cleared session history for {session_id}")
                return True
            return False

    async def get_session_info(self) -> dict[str, Any]:
        """
        Get session cache statistics for monitoring.

        Returns:
            Dictionary with cache statistics
        """
        async with self._cache_lock:
            return {
                "active_sessions": len(self._session_cache),
                "max_sessions": self._session_cache.maxsize,
                "ttl_seconds": self._session_cache.ttl,
                "max_history_length": self._max_history_length,
            }

    async def cleanup_expired_sessions(self) -> int:
        """
        Manually trigger cleanup of expired sessions.
        TTLCache handles this automatically, but this can be called explicitly.

        Returns:
            Number of sessions remaining after cleanup
        """
        async with self._cache_lock:
            # TTLCache automatically removes expired entries on access
            # Force cleanup by accessing all keys
            _ = list(self._session_cache.keys())
            remaining = len(self._session_cache)
            logger.debug(f"Session cleanup complete: {remaining} active sessions")
            return remaining
