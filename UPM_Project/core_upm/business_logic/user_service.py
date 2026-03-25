from os import name
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import authenticate # للاستخدام في منطق تسجيل الدخول
from core_upm.repositories import UserRepository # استيراد الـ Repository
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(name)


class UserService:
    """
    Handles user authentication and registration logic. 
    Uses UserRepository for data access.
    """
    def __init__(self):
        self.user_repo = UserRepository()
    
    def register_new_user(self, user_data: dict, password: str) -> User:
        """
        Applies registration rules and uses the repository to create the user.
        """
        if self.user_repo.user_exists_by_username(user_data['username']):
            raise ValidationError("Username already taken.")
        if self.user_repo.user_exists_by_email(user_data['email']):
            raise ValidationError("A user with that email already exists.")
            
        try:
            # Use repository to handle creation and password hashing
            user = self.user_repo.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=password
            )
            return user
        except Exception as e:
            logger.error(f"User registration error: {e}")
            # Re-raise as a generic validation error for the view to catch
            raise ValidationError(f"Registration failed: {str(e)}")

    def authenticate_user(self, username_or_email: str, password: str) -> User:
        """
        Authenticates user credentials. Accepts either username or email.
        """
        # Try to authenticate with username first
        user = authenticate(username=username_or_email, password=password)

        # If that fails and input looks like an email, try with email
        if user is None and '@' in username_or_email:
            try:
                from django.contrib.auth.models import User
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user is None or not user.is_active:
            raise PermissionDenied("invalid data")

        return user