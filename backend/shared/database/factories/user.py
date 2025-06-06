from sqlalchemy import func, select

from shared.database.factories.base import BaseFactory
from shared.database.models.user import User


class UserFactory(BaseFactory[User]):
    def __init__(self, db):
        super().__init__(model=User, db=db)

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt. TODO: implement proper hashing."""
        import hashlib

        return f"$2b$12${hashlib.md5(password.encode()).hexdigest()}"

    def get_unique_email(self, base_email: str = None) -> str:
        """Generate a unique email that doesn't exist in the database."""
        if base_email is None:
            base_email = self.faker.email()

        # Check if email exists
        query = select(func.count(User.id)).where(User.email == base_email)
        result = self.db.execute(query)
        count = result.scalar()

        if count == 0:
            return base_email

        # If exists, generate a unique one with counter
        base_name, domain = base_email.split("@")
        counter = 1
        while True:
            unique_email = f"{base_name}+{counter}@{domain}"
            query = select(func.count(User.id)).where(User.email == unique_email)
            result = self.db.execute(query)
            if result.scalar() == 0:
                return unique_email
            counter += 1

    def get_unique_username(self, base_username: str = None) -> str:
        """Generate a unique username that doesn't exist in the database."""
        if base_username is None:
            base_username = self.faker.user_name()

        # Ensure username fits in 50 char limit
        base_username = base_username[:45]  # Leave room for counter

        # Check if username exists
        query = select(func.count(User.id)).where(User.username == base_username)
        result = self.db.execute(query)
        count = result.scalar()

        if count == 0:
            return base_username

        # If exists, generate a unique one with counter
        counter = 1
        while True:
            unique_username = f"{base_username}{counter}"
            if len(unique_username) > 50:
                # If too long, truncate base and try again
                base_username = base_username[: -len(str(counter))]
                unique_username = f"{base_username}{counter}"

            query = select(func.count(User.id)).where(User.username == unique_username)
            result = self.db.execute(query)
            if result.scalar() == 0:
                return unique_username
            counter += 1

    def get_default_attributes(self) -> dict:
        """Generate default attributes for a new user."""
        email = self.get_unique_email()
        username = self.get_unique_username()

        return {
            "email": email,
            "username": username,
            "hashed_password": self.hash_password("password123"),
        }

    def create_with_password(self, password: str, **kwargs) -> User:
        """Create a user with a specific password."""
        kwargs["hashed_password"] = self.hash_password(password)
        return self.create(**kwargs)
