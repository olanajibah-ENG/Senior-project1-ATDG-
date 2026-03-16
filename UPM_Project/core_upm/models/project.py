from django.db import models
from django.contrib.auth.models import User # استيراد النموذج من نفس الحزمة
import uuid
class Project(models.Model):
    project_id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,verbose_name="Project ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='projects',verbose_name="Creation User", null=True, blank=True) # FK UserID
    project_name = models.CharField(max_length=255,verbose_name="Project Name")
    project_description = models.TextField( blank=True,verbose_name="Project Description")
    creation_date = models.DateTimeField(auto_now_add=True,verbose_name="Creation Date")
    last_modified_date = models.DateTimeField(auto_now=True,verbose_name="Last Modified Date")
    
    def __str__(self):
        return self.project_name
    
    class Meta:
        verbose_name="Project"
        verbose_name_plural="Projects"
        ordering=['-creation_date']