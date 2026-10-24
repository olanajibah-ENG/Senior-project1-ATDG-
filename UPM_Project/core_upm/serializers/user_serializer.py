from rest_framework import serializers
from django.contrib.auth.models import User
from core_upm.models.user import UserProfile, Role

class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role Model, including permissions_list."""
    class Meta:
        model = Role
        # is_system_user removed
        fields = ['role_id', 'role_name', 'description', 'permissions_list'] 
        read_only_fields = ['role_id']

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


class UserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_type = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'is_active',
            'date_joined',
            'full_name',
            'role_type',
            'is_online',
            'last_seen',
            'projects_count',
        ]

    def get_full_name(self, obj):
        try:
            return obj.profile.full_name
        except Exception:
            return ''

    def get_role_type(self, obj):
        try:
            return obj.profile.role_type
        except Exception:
            return 'DEVELOPER'

    def get_is_online(self, obj):
        try:
            return obj.profile.is_online
        except Exception:
            return False

    def get_last_seen(self, obj):
        try:
            return obj.profile.last_seen
        except Exception:
            return None

    def get_projects_count(self, obj):
        try:
            return obj.projects.count()
        except Exception:
            return 0


# ReviewerCreateSerializer — الصح
class ReviewerCreateSerializer(serializers.Serializer):
    # مو ModelSerializer لأن full_name مو في User
    username  = serializers.CharField(max_length=150)
    email     = serializers.EmailField()
    password  = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with that email already exists."
            )
        return value

    def create(self, validated_data):
        password  = validated_data.pop('password')
        full_name = validated_data.pop('full_name')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            is_active=True,
            )

        try:
            reviewer_role = Role.objects.get(role_type='REVIEWER')
        except Role.DoesNotExist:
            user.delete()  # rollback
            raise serializers.ValidationError(
                "REVIEWER role not found. Run setup_roles first."
            )

        profile = user.profile
        profile.role      = reviewer_role
        profile.full_name = full_name
        profile.save()

        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_new_password = data.get('confirm_new_password')

        if new_password != confirm_new_password:
            raise serializers.ValidationError("New passwords do not match.")
        if new_password == old_password:
            raise serializers.ValidationError("New password cannot be the same as the current password.")
        if new_password is None or len(new_password) < 8:
            raise serializers.ValidationError("New password must be at least 8 characters long.")
        return data
