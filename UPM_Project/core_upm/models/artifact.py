from django.db import models
import uuid
from .project import Project # استيراد نموذج Project

class CodeArtifact(models.Model):
    code_id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,verbose_name="code ID")
    project= models.ForeignKey(Project, on_delete=models.CASCADE,related_name='code_artifacts',verbose_name="project", null=True, blank=True) # FK ProjectID
    file_name = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True,verbose_name="Upload Date")
    code_language = models.CharField(max_length=50,verbose_name="Code Language")
    code_version = models.CharField(max_length=50,blank=True,null=True,verbose_name="Code Version")
    storage_reference=models.CharField(max_length=512,null=True,blank=True,verbose_name="Storage Reference")

    
    def __str__(self):
        return f"{self.file_name} ({self.project.project_name})"
    
    class Meta:
        verbose_name="Code Artifact"
        verbose_name_plural="Code Artifacts"
        ordering=['-upload_date']