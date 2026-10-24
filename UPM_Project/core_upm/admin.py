from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from core_upm.models.user import Role, UserProfile
from core_upm.models.project import Project
from core_upm.models.artifact import CodeArtifact

# ------------------
# 1. Inline UserProfile for User Admin
# ------------------

class UserProfileInline(admin.StackedInline):
    """
    Allows editing UserProfile directly from the User creation/edit page.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    # Define fields to display/edit
    fields = ('full_name', 'role', 'signup_date')
    readonly_fields = ('signup_date',)

# ------------------
# 2. Custom User Admin
# ------------------

class UserAdmin(BaseUserAdmin):
    """
    Redefines the User admin to include the UserProfile inline.
    """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    
    # Custom method to display the role from the UserProfile
    def get_role(self, obj):
        return obj.profile.role.role_name if hasattr(obj, 'profile') and obj.profile.role else 'N/A'
    get_role.short_description = 'System Role'

# Unregister the default User model admin first
admin.site.unregister(User)

# Register the custom User admin
admin.site.register(User, UserAdmin)

# ------------------
# 3. Standard Model Registration
# ------------------

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'description', 'permissions_list')
    search_fields = ('role_name',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_id', 'project_name', 'user', 'creation_date', 'last_modified_date')
    search_fields = ('project_name', 'user__username')
    list_filter = ('creation_date', 'last_modified_date')
    readonly_fields = ('project_id', 'creation_date', 'last_modified_date')

@admin.register(CodeArtifact)
class CodeArtifactAdmin(admin.ModelAdmin):
    list_display = ('code_id', 'file_name', 'project', 'code_language', 'upload_date', 'storage_reference')
    search_fields = ('file_name', 'project__project_name', 'code_language')
    list_filter = ('code_language', 'upload_date')
    readonly_fields = ('code_id', 'upload_date', 'storage_reference')