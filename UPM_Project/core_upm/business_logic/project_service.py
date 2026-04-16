from django.core.exceptions import PermissionDenied
# الاستيراد من طبقة Repositories
from core_upm.repositories import ProjectRepository
# الاستيراد من طبقة النماذج
from django.contrib.auth.models import User
from core_upm.models.project import Project

class ProjectService:
    """
    Handles project business logic, validation, and permission checks.
    Uses ProjectRepository for data access.
    """
    def __init__(self):
        self.project_repo = ProjectRepository()
    
    def create_new_project(self, user: User, data: dict) -> Project:
        """Creates a new project for the authenticated user."""
        return self.project_repo.create_project(
            user=user,
            name=data['project_name'],
            description=data.get('project_description', '')
        )

    def get_user_projects(self, user: User):
        """Retrieves all projects owned by the user."""
        return self.project_repo.get_projects_by_user(user)

    def get_project_details_if_authorized(self, user: User, project_id: str) -> Project:
        """Retrieves a project only if the user is the owner."""
        project = self.project_repo.get_project_by_id(project_id)
        if project.user != user:
            raise PermissionDenied("Access denied to this project.")
        return project

    # 👈 إضافة جديدة: لتحديث المشروع
    def update_project(self, project: Project, data: dict, user: User) -> Project:
        """Updates project details after verifying ownership."""
        if project.user != user:
            raise PermissionDenied("You don't have permission to update this project.")

        return self.project_repo.update_project(
            project=project,
            name=data.get('project_name'),
            description=data.get('project_description')
        )

    # 👈 إضافة جديدة: لحذف المشروع
    def delete_project(self, project_id: str, user: User) -> None:
        """Retrieves and deletes the project only if the user is the owner."""
        # نستغل دالة get_project_details_if_authorized للتحقق من الصلاحيات
        project = self.get_project_details_if_authorized(user, project_id)
            
        self.project_repo.delete_project(project)