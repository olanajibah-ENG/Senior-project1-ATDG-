from django.db import models
from core_upm.models.project import Project
import uuid
from .folder import Folder
from .version import Version


class CodeArtifact(models.Model):
    code_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4,
        editable=False, verbose_name="Code ID"
    )
    folder = models.ForeignKey(
        Folder, on_delete=models.CASCADE,
        related_name='code_artifacts', verbose_name="Folder",
        null=True, blank=True   # null=True لأن الصفوف القديمة في DB ليس لها folder
    )
    version = models.ForeignKey(
        Version, on_delete=models.CASCADE,
        related_name='code_artifacts', verbose_name="Version",
        null=True, blank=True   # null=True لأن الصفوف القديمة في DB ليس لها version FK
    )
    file_name = models.CharField(max_length=255, verbose_name="File Name")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="Upload Date")
    # تم حذف "language" لأنه مكرر مع "code_language"
    # تم حذف "file_path" لأنه غير موجود في الـ migration ولا الـ serializer
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='artifacts', null=True, blank=True)
    code_language = models.CharField(max_length=50, verbose_name="Code Language")

    # يشير للـ MongoDB GridFS ID
    storage_reference = models.CharField(
        max_length=512, null=True, blank=True,
        verbose_name="Storage Reference (GridFS ID)"
    )

    def __str__(self):
        return f"{self.file_name} (v{self.version.version_number})"

    class Meta:
        verbose_name = "Code Artifact"
        verbose_name_plural = "Code Artifacts"
        ordering = ['-upload_date']