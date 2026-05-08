from django.shortcuts import get_object_or_404
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
        """
        Retrieves all projects owned by a specific user.
        ✅ select_related('user') يجلب بيانات المستخدم في نفس الـ query
           بدل ما يعمل query منفصل لكل مشروع (N+1 problem)
        """
        return (
            Project.objects
            .filter(user=user)
            .select_related('user')
            .only(
                'project_id',
                'project_name',
                'project_description',
                'creation_date',
                'last_modified_date',
                'source_type',
                'user__id',
                'user__username',
                'user__email',
            )
            .order_by('-creation_date')
        )

    def get_project_by_id(self, project_id: str) -> Project:
        """Retrieves a single project by ID or raises 404."""
        return get_object_or_404(
            Project.objects.select_related('user'),
            project_id=project_id
        )

    def update_project(self, project: Project, name: str = None, description: str = None) -> Project:
        """Updates project details."""
        if name is not None:
            project.project_name = name
        if description is not None:
            project.project_description = description
        project.save()
        return project

    def delete_project(self, project: Project) -> None:
        """Deletes a specific Project instance."""
        project.delete()