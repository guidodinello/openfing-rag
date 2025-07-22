from sqlalchemy.orm import Session

from shared.database.models import User
from shared.database.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)
