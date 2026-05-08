from rest_framework_simplejwt.tokens import RefreshToken


class RoleAwareRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        try:
            profile = user.profile
            token["role_type"] = profile.role_type
            token["full_name"] = profile.full_name
            token["user_id"] = user.id
        except Exception:
            token["role_type"] = "DEVELOPER"
            token["full_name"] = user.username
            token["user_id"] = user.id
        return token
