from rest_framework import serializers
from django.contrib.auth.models import User
from core_upm.models.user import UserProfile, Role

class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role Model, including permissions_list."""
    class Meta:
        model = Role
        # is_system_user removed
        fields = ['id', 'role_name', 'description', 'permissions_list'] 
        read_only_fields = ['id']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model (Nested for UserSerializer)."""
    role = RoleSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['full_name', 'signup_date', 'role']
        read_only_fields = fields

class UserSerializer(serializers.ModelSerializer):
    """Serializer for reading/displaying user data post-login/registration."""
    profile = UserProfileSerializer(read_only=True) # Nested profile data

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']
        read_only_fields = fields

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration (Sign Up).
    Only validates required fields, actual creation/hashing happens in UserService.
    """
    class Meta:
        model = User
        # Only include fields required for Sign Up
        fields = ['username', 'email', 'password'] 
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'email': {'required': True} # Enforcing email as required for registration
        }
        
    def validate_email(self, value):
        # Ensure email is unique
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("existing email!!")
        return value
    
    def validate(self, data):
        # Check for empty fields
        for field_name, field_value in data.items():
            if field_value is None or (isinstance(field_value, str) and field_value.strip() == ''):
                raise serializers.ValidationError("a field is missing")
        return data