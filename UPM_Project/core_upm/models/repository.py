from django.db import models
import uuid
from .project import Project


class Repository(models.Model):
    repo_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4,
        editable=False, verbose_name="Repo ID"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name='repositories', verbose_name="Project"
    )
    repo_name = models.CharField(max_length=255, verbose_name="Repo Name")
    source_type = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Source Type"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"{self.repo_name} ({self.project.project_name})"

    class Meta:
        verbose_name = "Repository"
        verbose_name_plural = "Repositories"
        ordering = ['-created_at']