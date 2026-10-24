from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

class UserRepository:
    """Handles direct database access for User and UserProfile models."""
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """Creates and saves a new User instance (password is hashed by create_user)."""
        return User.objects.create_user(username=username, email=email, password=password)

    def get_user_by_username(self, username: str) -> User:
        """Retrieves a User instance by username."""
        return get_object_or_404(User, username=username)

    def user_exists_by_email(self, email: str) -> bool:
        """Checks if a user exists with the given email."""
        return User.objects.filter(email=email).exists()

    def user_exists_by_username(self, username: str) -> bool:
        """Checks if a user exists with the given username."""
        return User.objects.filter(username=username).exists()
