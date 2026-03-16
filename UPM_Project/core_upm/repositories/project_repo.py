from django.shortcuts import get_object_or_404
# الاستيراد من طبقة النماذج
from core_upm.models.project import Project
from django.contrib.auth.models import User
from django.db.models import QuerySet

class ProjectRepository:
    """Handles direct database access for Project model."""
    
    def create_project(self, user: User, name: str, description: str = '') -> Project:
        """Creates a new Project instance."""
        return Project.objects.create(
            user=user,
            project_name=name,
            project_description=description
        )

    def get_projects_by_user(self, user: User) -> QuerySet[Project]:
        """Retrieves all projects owned by a specific user."""
        return Project.objects.filter(user=user).order_by('-creation_date')

    def get_project_by_id(self, project_id: str) -> Project:
        """Retrieves a single project by ID or raises 404."""
        return get_object_or_404(Project, project_id=project_id)
        
    # 👈 إضافة جديدة: لتحديث بيانات المشروع
    def update_project(self, project: Project, name: str = None, description: str = None) -> Project:
        """Updates project details."""
        if name is not None:
            project.project_name = name
        if description is not None:
            project.project_description = description
        
        project.save()
        return project

    # 👈 إضافة جديدة: لحذف المشروع
    def delete_project(self, project: Project) -> None:
        """Deletes a specific Project instance."""
        project.delete()