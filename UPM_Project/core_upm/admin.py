# UPM_Project/core_upm/admin.py
# حُذف منه: import CodeArtifact و CodeArtifactAdmin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from core_upm.models.user import Role, UserProfile
from core_upm.models.project import Project


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('full_name', 'role', 'signup_date')
    readonly_fields = ('signup_date',)


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')

    def get_role(self, obj):
        return obj.profile.role.role_name if hasattr(obj, 'profile') and obj.profile.role else 'N/A'
    get_role.short_description = 'System Role'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'description')
    search_fields = ('role_name',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_id', 'project_name', 'user', 'creation_date')
    search_fields = ('project_name', 'user__username')
    readonly_fields = ('project_id', 'creation_date', 'last_modified_date')