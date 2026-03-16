import logging
from notification_service.celery_app import app
from notifications.notification_service import SimpleNotification
from notifications.models import Notification
from django.utils import timezone

logger = logging.getLogger(__name__)

@app.task(bind=True)
def send_project_notification_task(self, notification_id, user_email, action, project_name, **kwargs):
    try:
        # جلب السجل الموجود بدلاً من إنشاء واحد جديد
        notification = Notification.objects.get(id=notification_id)
        
        notification_obj = SimpleNotification.create_project_notification(
            user_email=user_email, action=action, project_name=project_name
        )
        notification_obj.send_email()
        
        # تحديث السجل نفسه
        notification.status = 'SENT'
        notification.sent_at = timezone.now()
        notification.save()
        return {"status": "success"}
    except Exception as e:
        notification = Notification.objects.get(id=notification_id)
        notification.status = 'FAILED'
        notification.error_message = str(e)
        notification.save()
        raise e

@app.task(bind=True)
def send_code_notification_task(self, notification_id, user_email, action, code_name, project_name, **kwargs):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification_obj = SimpleNotification.create_code_notification(
            user_email=user_email, action=action, code_name=code_name, project_name=project_name
        )
        notification_obj.send_email()
        notification.status = 'SENT'
        notification.save()
    except Exception as e:
        notification = Notification.objects.get(id=notification_id)
        notification.status = 'FAILED'
        notification.save()

@app.task(bind=True)
def send_documentation_notification_task(self, notification_id, user_email, file_name, file_type, **kwargs):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification_obj = SimpleNotification.create_documentation_notification(
            user_email=user_email, file_name=file_name, file_type=file_type
        )
        notification_obj.send_email()
        notification.status = 'SENT'
        notification.save()
    except Exception as e:
        notification = Notification.objects.get(id=notification_id)
        notification.status = 'FAILED'
        notification.save()

@app.task(bind=True)
def send_custom_notification_task(self, notification_id, user_email, title, message, notification_type, **kwargs):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification_obj = SimpleNotification(
            user_email=user_email, title=title, message=message, notification_type=notification_type
        )
        notification_obj.send_email()
        notification.status = 'SENT'
        notification.save()
    except Exception as e:
        notification = Notification.objects.get(id=notification_id)
        notification.status = 'FAILED'
        notification.save()