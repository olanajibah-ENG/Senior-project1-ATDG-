"""
Notification Models - نماذج الإشعارات
AutoTest & DocGen Notification Service
"""

from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """
    Model لتخزين الإشعارات في قاعدة البيانات
    """
    
    NOTIFICATION_TYPES = [
        ('PROJECT_CREATED', 'Project Created'),
        ('PROJECT_DELETED', 'Project Deleted'),
        ('CODE_ADDED', 'Code Added'),
        ('CODE_DELETED', 'Code Deleted'),
        ('DOCUMENTATION_EXPORTED', 'Documentation Exported'),
        ('SYSTEM_ALERT', 'System Alert'),
        ('USER_REGISTERED', 'User Registered'),
        ('PASSWORD_CHANGED', 'Password Changed'),
        ('CODE_ANALYZED', 'Code Analyzed'),
        ('CUSTOM', 'Custom Notification'),
        ('REVIEWER_ALERT', 'Reviewer Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),  # 🆕 لـ Celery
        ('SENT', 'Sent'),
        ('READ', 'Read'),
        ('FAILED', 'Failed'),
    ]
    
    # User information
    user_email = models.EmailField(max_length=254, db_index=True)
    user_name = models.CharField(max_length=255, blank=True, default='')
    user_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # Optional: store user ID from UPM
    
    # Notification content
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='CUSTOM')
    
    # Related information
    related_id = models.CharField(max_length=255, blank=True, null=True)  # ID of related item (project, code, etc.)
    related_type = models.CharField(max_length=50, blank=True, null=True)  # Type: 'project', 'code', 'documentation', etc.
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='MEDIUM')
    
    # Action information (for frontend)
    action_url = models.CharField(max_length=500, blank=True, null=True)  # URL to navigate when clicked
    action_text = models.CharField(max_length=100, blank=True, null=True)  # Text for action button
    
    # Read status
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Email sending
    send_attempts = models.IntegerField(default=0)
    email_sent = models.BooleanField(default=False)
    
    # 🆕 Celery Task Tracking
    task_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # Celery task ID
    error_message = models.TextField(blank=True, null=True)  # Error message if task failed
    
    # Extra data (JSON field for flexible data storage)
    extra_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_email', '-created_at']),
            models.Index(fields=['user_id', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user_email} ({self.status})"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.status = 'READ'
            self.save(update_fields=['is_read', 'read_at', 'status'])
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        if not self.email_sent:
            self.email_sent = True
            self.sent_at = timezone.now()
            self.status = 'SENT'
            self.save(update_fields=['email_sent', 'sent_at', 'status'])
