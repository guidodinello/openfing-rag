from shared.database.factories import UserFactory
from shared.database.models import User
from shared.database.seeders import BaseSeeder


class UserSeeder(BaseSeeder):
    async def run(self):
        """Seed the database with specific users for development/testing."""

        # Create specific users for development
        users_data = [
            {
                "email": "admin@openfing.edu.uy",
                "username": "admin",
                "hashed_password": "hash-XXX",  # TODO: implement
                "is_active": True,
                "is_superuser": True,
            },
            {
                "email": "teacher@openfing.edu.uy",
                "username": "teacher",
                "hashed_password": "hash-XXX",
                "is_active": True,
                "is_superuser": False,
            },
            {
                "email": "student@openfing.edu.uy",
                "username": "student",
                "hashed_password": "hash-XXX",
                "is_active": True,
                "is_superuser": False,
            },
            {
                "email": "demo@openfing.edu.uy",
                "username": "demo",
                "hashed_password": "hash-XXX",
                "is_active": True,
                "is_superuser": False,
            },
            {
                "email": "inactive@openfing.edu.uy",
                "username": "inactive_user",
                "hashed_password": "hash-XXX",
                "is_active": False,
                "is_superuser": False,
            },
        ]

        created_users = []
        for user_data in users_data:
            user = User(**user_data)
            self.db.add(user)
            created_users.append(user)

        await self.db.flush()
        return created_users

    async def run_random(self):
        """Create random users using the factory."""
        factory = UserFactory(db=self.db)

        users = []
        special_user = await factory.create_with_password(
            "specialpassword123",
            email="special@example.com",
            username="special_user",
        )
        users.append(special_user)

        return users
