import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationClient:
    """
    Client for sending notifications to notification service
    """

    NOTIFICATION_SERVICE_URL = getattr(
        settings, 'NOTIFICATION_SERVICE_URL', 'http://notification_django_app:8000'
    )

    @staticmethod
    def _get_notification_url(endpoint):
        """Create full URL for notification service"""
        return f"{NotificationClient.NOTIFICATION_SERVICE_URL}/api/notifications/{endpoint}/"

    @staticmethod
    def _send_notification_request(endpoint, data):
        """
        Send HTTP request to notification service.

        ✅ timeout خُفِّض من 10 ثوانٍ لـ 3 ثوانٍ:
           الإشعارات ليست حرجة — لو الـ service بطيئة نسجّل الخطأ ونكمل.
           هذا يمنع blocking الـ workers عند ضغط عالي.
        """
        try:
            url = NotificationClient._get_notification_url(endpoint)
            response = requests.post(url, json=data, timeout=3)   # ✅ 3s بدل 10s

            if response.status_code in [200, 201]:
                logger.info(
                    f"✅ Notification sent successfully: {endpoint} "
                    f"- {data.get('user_email', 'N/A')}"
                )
                return True
            else:
                logger.error(
                    f"❌ Failed to send notification: {endpoint} "
                    f"- Status: {response.status_code} - Response: {response.text}"
                )
                return False

        except requests.Timeout:
            # ✅ timeout منفصل عن باقي الأخطاء للوضوح في الـ logs
            logger.warning(
                f"⏱ Notification timeout (3s exceeded): {endpoint} "
                f"- {data.get('user_email', 'N/A')} — notification skipped"
            )
            return False

        except requests.ConnectionError:
            logger.warning(
                f"🔌 Notification service unreachable: {endpoint} "
                f"— notification skipped"
            )
            return False

        except requests.RequestException as e:
            logger.error(f"❌ Error connecting to notification service: {str(e)}")
            return False

        except Exception as e:
            logger.error(f"❌ Unexpected error in sending notification: {str(e)}")
            return False

    @staticmethod
    def send_project_notification(user_email, action, project_name, project_id='', user_name=''):
        data = {
            'user_email':   user_email,
            'action':       action,
            'project_name': project_name,
            'project_id':   project_id,
            'user_name':    user_name
        }
        return NotificationClient._send_notification_request('project', data)

    @staticmethod
    def send_code_notification(user_email, action, code_name, project_name, code_id='', user_name=''):
        data = {
            'user_email':   user_email,
            'action':       action,
            'code_name':    code_name,
            'project_name': project_name,
            'code_id':      code_id,
            'user_name':    user_name
        }
        return NotificationClient._send_notification_request('code', data)

    @staticmethod
    def send_user_notification(user_email, action, user_name=''):
        data = {
            'user_email': user_email,
            'action':     action,
            'user_name':  user_name
        }
        return NotificationClient._send_notification_request('user', data)

    @staticmethod
    def send_custom_notification(user_email, title, message, notification_type='SYSTEM_ALERT', user_name=''):
        data = {
            'user_email':        user_email,
            'title':             title,
            'message':           message,
            'notification_type': notification_type,
            'user_name':         user_name
        }
        return NotificationClient._send_notification_request('custom', data)

    @staticmethod
    def send_system_alert(user_email, alert_type, message, user_name=''):
        data = {
            'user_email': user_email,
            'alert_type': alert_type,
            'message':    message,
            'user_name':  user_name
        }
        return NotificationClient._send_notification_request('system', data)