import hashlib
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response

from shared.enums import CustomHeaders


def get_client_ip(request: Request) -> str:
    """Extract real client IP considering proxies."""
    if forwarded_for := request.headers.get(CustomHeaders.FORWARDED_FOR):
        return forwarded_for.split(",")[0].strip()
    if real_ip := request.headers.get(CustomHeaders.REAL_IP):
        return real_ip
    return request.client.host if request.client else "unknown"


def build_auth_context(request: Request) -> dict[str, Any]:
    """Authentication context for logging"""
    context: dict[str, Any] = {"auth_type": None}

    if api_key := request.headers.get(CustomHeaders.API_KEY):
        context.update(
            {
                "auth_type": "api_key",
                "api_key_hash": hash_sensitive_data(api_key),
            },
        )

    elif auth_header := request.headers.get(CustomHeaders.AUTHORIZATION):
        if auth_header.startswith("Bearer "):
            context.update(
                {
                    "auth_type": "bearer_token",
                    "token_hash": hash_sensitive_data(auth_header.replace("Bearer ", "")),
                },
            )

    return context


def hash_sensitive_data(data: str) -> str:
    """Create a safe, loggable hash"""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


CallNext = Callable[[Request], Awaitable[Response]]
