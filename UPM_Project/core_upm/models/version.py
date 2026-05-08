from django.db import models
import uuid
from .project import Project


class Version(models.Model):
    version_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4,
        editable=False, verbose_name="Version ID"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name='versions', verbose_name="Project"
    )
    version_number = models.IntegerField(default=1, verbose_name="Version Number")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    def __str__(self):
        return f"v{self.version_number} - {self.project.project_name}"

    class Meta:
        verbose_name = "Version"
        verbose_name_plural = "Versions"
        ordering = ['-created_at']
        unique_together = [['project', 'version_number']]