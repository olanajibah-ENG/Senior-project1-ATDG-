import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationClient:
    """
    عميل لإرسال الإشعارات إلى خدمة الإشعارات
    """

    NOTIFICATION_SERVICE_URL = getattr(settings, 'NOTIFICATION_SERVICE_URL', 'http://notification_django_app:8000')

    @staticmethod
    def _get_notification_url(endpoint):
        """إنشاء URL كامل لخدمة الإشعارات"""
        return f"{NotificationClient.NOTIFICATION_SERVICE_URL}/api/notifications/{endpoint}/"

    @staticmethod
    def _send_notification_request(endpoint, data):
        """
        إرسال طلب HTTP إلى خدمة الإشعارات

        Args:
            endpoint (str): نقطة النهاية (مثل 'code', 'documentation', إلخ)
            data (dict): بيانات الإشعار

        Returns:
            bool: نجاح أو فشل الإرسال
        """
        try:
            url = NotificationClient._get_notification_url(endpoint)
            response = requests.post(url, json=data, timeout=10)

            if response.status_code in [200, 201]:
                logger.info(f"✅ تم إرسال إشعار بنجاح: {endpoint} - {data.get('user_email', 'N/A')}")
                return True
            else:
                logger.error(f"❌ فشل في إرسال الإشعار: {endpoint} - Status: {response.status_code} - Response: {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"❌ خطأ في الاتصال بخدمة الإشعارات: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع في إرسال الإشعار: {str(e)}")
            return False

    @staticmethod
    def send_code_notification(user_email, action, code_name, project_name, code_id='', user_name=''):
        """
        إرسال إشعار متعلق بالكود

        Args:
            user_email (str): البريد الإلكتروني للمستخدم
            action (str): الفعل ('added', 'deleted', 'analyzed', 'error')
            code_name (str): اسم الملف/الكود
            project_name (str): اسم المشروع
            code_id (str): معرف الكود (اختياري)
            user_name (str): اسم المستخدم (اختياري)
        """
        data = {
            'user_email': user_email,
            'action': action,
            'code_name': code_name,
            'project_name': project_name,
            'code_id': code_id,
            'user_name': user_name
        }
        return NotificationClient._send_notification_request('code', data)

    @staticmethod
    def send_documentation_notification(user_email, file_name, file_type, project_name='', user_name=''):
        """
        إرسال إشعار متعلق بتصدير التوثيق

        Args:
            user_email (str): البريد الإلكتروني للمستخدم
            file_name (str): اسم الملف المُصدّر
            file_type (str): نوع الملف ('pdf', 'html', 'md', إلخ)
            project_name (str): اسم المشروع (اختياري)
            user_name (str): اسم المستخدم (اختياري)
        """
        data = {
            'user_email': user_email,
            'file_name': file_name,
            'file_type': file_type,
            'project_name': project_name,
            'user_name': user_name
        }
        return NotificationClient._send_notification_request('documentation', data)

    @staticmethod
    def send_custom_notification(user_email, title, message, notification_type='SYSTEM_ALERT', user_name=''):
        """
        إرسال إشعار مخصص

        Args:
            user_email (str): البريد الإلكتروني للمستخدم
            title (str): عنوان الإشعار
            message (str): محتوى الإشعار
            notification_type (str): نوع الإشعار (اختياري)
            user_name (str): اسم المستخدم (اختياري)
        """
        data = {
            'user_email': user_email,
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'user_name': user_name
        }
        return NotificationClient._send_notification_request('custom', data)

    @staticmethod
    def send_system_alert(user_email, alert_type, message, user_name=''):
        """
        إرسال تنبيه نظامي

        Args:
            user_email (str): البريد الإلكتروني للمستخدم
            alert_type (str): نوع التنبيه ('error', 'warning', 'info', 'success')
            message (str): رسالة التنبيه
            user_name (str): اسم المستخدم (اختياري)
        """
        data = {
            'user_email': user_email,
            'alert_type': alert_type,
            'message': message,
            'user_name': user_name
        }
        return NotificationClient._send_notification_request('system', data)
