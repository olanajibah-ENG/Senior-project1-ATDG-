from django.db import models
import uuid
from .repository import Repository
from .project import Project


class Folder(models.Model):
    folder_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4,
        editable=False, verbose_name="Folder ID"
    )
    repo = models.ForeignKey(
        Repository, on_delete=models.SET_NULL,
        related_name='folders', verbose_name="Repository",
        null=True, blank=True  # nullable كما يشير ERD — الـ Folder ممكن يكون بدون Repository
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name='folders', verbose_name="Project"
    )
    parent_folder = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subfolders', verbose_name="Parent Folder"
    )
    folder_name = models.CharField(max_length=255, verbose_name="Folder Name")
    folder_path = models.CharField(max_length=1024, verbose_name="Folder Path")

    def __str__(self):
        return self.folder_path

    class Meta:
        verbose_name = "Folder"
        verbose_name_plural = "Folders"
        ordering = ['folder_path']