from shared.database.factories import UserFactory
from shared.database.repositories import UserRepository
from shared.database.seeders.base import BaseSeeder


class UserSeeder(BaseSeeder):
    """Seeder for users using repository pattern."""

    def __init__(self, db, user_repo: UserRepository):
        super().__init__(db)
        self.user_repo = user_repo

    def run(self, count: int = 10) -> None:
        _ = self.user_repo.update_or_create_by_email(
            email="special@example.com",
            username="special_user",
            hashed_password="$2b$12$special_hashed_password_here",
        )

        _ = UserFactory(db=self.db).create_batch(count=count)
