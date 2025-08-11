from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.database.models import ApiKey
from shared.database.repositories import BaseRepository


class ApiKeyRepository(BaseRepository[ApiKey]):
    def __init__(self, db: Session):
        super().__init__(ApiKey, db)

    def get_by_hash(self, hashed_api_key: str) -> ApiKey | None:
        """Get API key record by hashed key"""
        return self.get_by(key_hash=hashed_api_key)

    def get_by_user(self, user_id: int) -> list[ApiKey]:
        """Get all API keys for a user"""
        return self.db.execute(select(self.model).where(self.model.user_id == user_id)).scalars().all()
