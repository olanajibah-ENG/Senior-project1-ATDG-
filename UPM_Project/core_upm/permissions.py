from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = "Admin access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            return getattr(user.profile, "role_type", None) == "ADMIN"
        except Exception:
            return False


class IsReviewerRole(BasePermission):
    message = "Reviewer access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            return getattr(user.profile, "role_type", None) == "REVIEWER"
        except Exception:
            return False


class IsDeveloperRole(BasePermission):
    message = "Developer access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            return getattr(user.profile, "role_type", None) == "DEVELOPER"
        except Exception:
            return False


class IsAdminOrReviewer(BasePermission):
    message = "Admin or Reviewer access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            return getattr(user.profile, "role_type", None) in ["ADMIN", "REVIEWER"]
        except Exception:
            return False
