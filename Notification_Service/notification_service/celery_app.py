"""
Celery Configuration for Notification Service
تكوين Celery للخدمة - مثل الـ AI Service
"""

import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_service.settings')

# Create Celery app instance
app = Celery('notification_service')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """
    Debug task for testing Celery connection
    """
    print(f'Request: {self.request!r}')
