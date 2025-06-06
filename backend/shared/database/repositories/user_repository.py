from sqlalchemy.orm import Session

from shared.database.models.user import User
from shared.database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        return self.get_by(email=email)

    def get_by_username(self, username: str) -> User | None:
        return self.get_by(username=username)

    def update_or_create_by_email(self, email: str, **data) -> tuple[User, bool]:
        return self.update_or_create(data, email=email)

    def update_or_create_by_username(self, username: str, **data) -> tuple[User, bool]:
        return self.update_or_create(data, username=username)
