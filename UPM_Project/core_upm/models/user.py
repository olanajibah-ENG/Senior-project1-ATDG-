from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True,verbose_name="Role Name")
    description=models.TextField(blank=True,verbose_name="Role Description")
    permissions_list=models.JSONField(default=dict,verbose_name="Permissions List")
    
    def __str__(self):
        return self.role_name
    class Meta:
        verbose_name="Role"
        verbose_name_plural="Roles"

class UserProfile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,primary_key=True,related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="Default Role")
    full_name=models.CharField(max_length=255,verbose_name="Full Name")
    signup_date=models.DateTimeField(auto_now_add=True,verbose_name="Signup Date")
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name="User profile"
        verbose_name_plural="User Profiles"

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
       if created:
        # UserProfile يتطلب Full Name. يمكننا تعبئته بقيمة افتراضية أو استخدام اسم المستخدم
        # هنا نفترض عدم الحاجة لتعيين Role افتراضي (Null=True في النموذج)
        UserProfile.objects.create(
            user=instance, 
            full_name=instance.username 
        )