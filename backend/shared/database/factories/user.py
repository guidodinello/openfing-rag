import hashlib

from sqlalchemy import func, select

from shared.database.factories import BaseFactory
from shared.database.models import User


class UserFactory(BaseFactory[User]):
    def __init__(self, db):
        super().__init__(model=User, db=db)

    def _get_count(self, where) -> int:
        return self.db.execute(select(func.count(User.id)).where(where)).scalar()

    def hash_password(self, password: str) -> str:
        return f"faked_{hashlib.md5(password.encode()).hexdigest()}"

    def get_unique_email(self, base_email: str | None = None) -> str:
        """Generate a unique email that doesn't exist in the database."""
        base_email = base_email or self.faker.email()

        # Check if email exists
        if self.get_count(where=(User.email == base_email)) == 0:
            return base_email

        # If exists, generate a unique one with counter
        base_name, domain = base_email.split("@")
        counter = 1
        while True:
            unique_email = f"{base_name}+{counter}@{domain}"
            if self.get_count(where=(User.email == unique_email)) == 0:
                return unique_email
            counter += 1

    def get_unique_username(self, base_username: str | None = None) -> str:
        """Generate a unique username that doesn't exist in the database."""
        base_username = base_username or self.faker.user_name()
        # Ensure username fits in 50 char limit
        base_username = base_username[:45]

        if self.get_count(where=(User.username == base_username)) == 0:
            return base_username

        counter = 1
        while True:
            unique_username = f"{base_username}{counter}"
            if len(unique_username) > 50:
                base_username = base_username[: -len(str(counter))]
                unique_username = f"{base_username}{counter}"

            if self.get_count(where=(User.username == unique_username)) == 0:
                return unique_username
            counter += 1

    def get_default_attributes(self) -> dict:
        """Generate default attributes for a new user."""
        return {
            "email": self.get_unique_email(),
            "username": self.get_unique_username(),
            "hashed_password": self.hash_password("password123"),
        }

    def create_with_password(self, password: str, **kwargs) -> User:
        """Create a user with a specific password."""
        kwargs["hashed_password"] = self.hash_password(password)
        return self.create(**kwargs)
