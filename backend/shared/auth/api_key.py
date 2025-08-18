import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyHeader

from shared.config import get_settings
from shared.database.models import ApiKey as ApiKeyModel
from shared.database.models import ApiKeyScope, User
from shared.database.repository_dependencies import ApiKeyRepositoryDep
from shared.enums import CustomHeaders
from shared.exceptions.authentication_exception import AuthenticationException

settings = get_settings()

api_key_header = APIKeyHeader(
    name=CustomHeaders.API_KEY,
    description="API key for authentication. Contact admin for access.",
    auto_error=False,
)

ApiKey = Annotated[str, Depends(api_key_header)]


class HMACApiKeyService:
    """
    API Key service using HMAC-SHA256 for security and performance.
    """

    def __init__(self, api_key_repo: ApiKeyRepositoryDep):
        self.api_key_repo = api_key_repo

    @staticmethod
    def verify_api_key(self, plain_api_key: str, hashed_api_key: str) -> bool:
        """Uses constant-time comparison to prevent timing attacks."""
        expected_hash = HMACApiKeyService.hash_api_key(plain_api_key)
        return hmac.compare_digest(expected_hash, hashed_api_key)

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key using HMAC-SHA256 with server secret."""
        return hmac.new(
            settings.API_KEYS.HMAC_SECRET.encode("utf-8"),
            api_key.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _generate_plain_key(scope: ApiKeyScope) -> str:
        """Generate a new API key with proper entropy."""
        return f"{scope.value}_{secrets.token_urlsafe(32)}"

    def authenticated_key(self, api_key: str) -> ApiKeyModel:
        """Authenticate a user by api key"""
        if not api_key:
            raise AuthenticationException.missing_api_key()

        api_key_model = self.get_api_key(api_key)

        if not api_key_model:
            raise AuthenticationException.invalid_api_key()
        if api_key_model.is_expired:
            raise AuthenticationException.expired_api_key()
        if not api_key_model.is_valid:
            raise AuthenticationException.invalid_api_key()

        return api_key_model

    def register_api_key(
        self,
        user_id: int,
        name: str,
        scope: ApiKeyScope,
        expires_at: datetime | None = None,
    ) -> tuple[str, ApiKeyModel]:
        """Create a new API key for a user."""
        plain_value = HMACApiKeyService._generate_plain_key(scope)

        return plain_value, self.api_key_repo.create(
            user_id=user_id,
            name=name,
            key_hash=HMACApiKeyService.hash_api_key(plain_value),
            scope=scope,
            expires_at=expires_at,
        )

    def get_api_key(self, api_key: str) -> ApiKeyModel:
        return self.api_key_repo.get_by_hash(HMACApiKeyService.hash_api_key(api_key))


def get_hmac_api_key_service(api_key_repo: ApiKeyRepositoryDep) -> HMACApiKeyService:
    return HMACApiKeyService(api_key_repo)


ApiKeyServiceDep = Annotated[HMACApiKeyService, Depends(get_hmac_api_key_service)]


def get_authenticated_api_key(auth_service: ApiKeyServiceDep, api_key: ApiKey) -> User:
    return auth_service.authenticated_key(api_key)


AuthenticatedApiKey = Annotated[ApiKeyModel, Depends(get_authenticated_api_key)]


def require_read_permission(api_key: AuthenticatedApiKey) -> ApiKeyModel:
    if not api_key.has_permission(ApiKeyScope.READ):
        raise AuthenticationException.insufficient_permissions(ApiKeyScope.READ.value)
    return api_key


def require_write_permission(api_key: AuthenticatedApiKey) -> ApiKeyModel:
    if not api_key.has_permission(ApiKeyScope.WRITE):
        raise AuthenticationException.insufficient_permissions(ApiKeyScope.READ.write)
    return api_key


def require_admin_permission(api_key: AuthenticatedApiKey) -> ApiKeyModel:
    if not api_key.has_permission(ApiKeyScope.ADMIN):
        raise AuthenticationException.insufficient_permissions(ApiKeyScope.READ.admin)
    return api_key
