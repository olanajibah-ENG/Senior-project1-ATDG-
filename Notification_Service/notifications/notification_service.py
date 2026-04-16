"""
Notification Service - Simple email notification system without storage
AutoTest & DocGen Notification Service
"""

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


class SimpleNotification:
    """
    Simple notification system without database
    Focuses on email sending only with integration capabilities to other systems
    """

    # Supported notification types
    NOTIFICATION_TYPES = {
        'PROJECT_CREATED': 'New project created',
        'PROJECT_DELETED': 'Project deleted',
        'CODE_ADDED': 'New code added',
        'CODE_DELETED': 'Code deleted',
        'DOCUMENTATION_EXPORTED': 'Documentation file exported',
        'SYSTEM_ALERT': 'System alert',
        'USER_REGISTERED': 'New user registered',
        'PASSWORD_CHANGED': 'Password changed',
    }

    def __init__(self, user_email, notification_type, title, message,
                 user_name='', related_id='', related_type='', priority='MEDIUM',
                 extra_data=None):
        """
        Initialize notification

        Args:
            user_email (str): Recipient email
            notification_type (str): Notification type
            title (str): Notification title
            message (str): Notification message
            user_name (str): User name
            related_id (str): Related item ID
            related_type (str): Related item type
            priority (str): Priority level
            extra_data (dict): Extra data for integration with other systems
        """
        self.user_email = user_email
        self.user_name = user_name or 'Dear User'
        self.notification_type = notification_type
        self.title = title
        self.message = message
        self.related_id = related_id
        self.related_type = related_type
        self.priority = priority
        self.extra_data = extra_data or {}

        # System data
        self.created_at = timezone.now()
        self.status = 'PENDING'
        self.send_attempts = 0
        self.max_send_attempts = 3

    def send_email(self):
        """
        Send notification via email

        Returns:
            bool: True if sent successfully, False if failed
        """
        try:
            if self.send_attempts >= self.max_send_attempts:
                self.status = 'FAILED'
                return False

            # Check email validity
            if not self._is_valid_email(self.user_email):
                self.status = 'FAILED'
                return False

            # Prepare email content
            subject = f"[AutoTest & DocGen] {self.title}"
            plain_message = self._create_plain_message()
            html_message = self._create_html_message()

            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user_email],
                html_message=html_message,
                fail_silently=False,
            )

            self.status = 'SENT'
            return True

        except Exception as e:
            self.send_attempts += 1
            if self.send_attempts >= self.max_send_attempts:
                self.status = 'FAILED'
            print(f"Failed to send notification email: {e}")
            return False

    def _create_plain_message(self):
        """Create plain text message"""
        return f"""
Hello {self.user_name},

{self.message}

Best regards,
AutoTest & DocGen Team
{self.created_at.strftime('%Y-%m-%d %H:%M')}
        """.strip()

    def _create_html_message(self):
        """Create HTML message"""
        return f"""
<html>
<body dir="rtl" style="font-family: Arial, sans-serif; direction: rtl;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #5a3d9a, #7c4dff); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0; text-align: center;">{self.title}</h2>
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <p style="margin: 0 0 15px 0; line-height: 1.6; color: #333;">{self.message.replace(chr(10), '<br>')}</p>

            {self._create_extra_info_html()}

            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; text-align: center;">
                <p>Best regards,<br>AutoTest & DocGen Team</p>
                <p style="font-size: 12px;">{self.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            </div>
        </div>
    </div>
</body>
</html>
        """

    def _create_extra_info_html(self):
        """Create extra info HTML"""
        info_parts = []

        if self.related_id:
            info_parts.append(f"<strong>ID:</strong> {self.related_id}")

        if self.related_type:
            type_names = {
                'project': 'Project',
                'code': 'Code',
                'documentation': 'Documentation',
                'user': 'User'
            }
            type_name = type_names.get(self.related_type, self.related_type)
            info_parts.append(f"<strong>{type_name}:</strong> {self.related_type}")

        if info_parts:
            return f"""
            <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0; border-right: 4px solid #5a3d9a;">
                {'<br>'.join(info_parts)}
            </div>
            """

        return ""

    def _is_valid_email(self, email):
        """
        Check email validity
        Supports all email domains, not just Gmail
        """
        if not email or '@' not in email:
            return False

        local, domain = email.split('@', 1)

        # Check domain validity (basic check)
        if not domain or '.' not in domain or len(domain) < 4:
            return False

        # Check local part validity
        if not local or len(local) < 1 or len(local) > 64:
            return False

        # Check for suspicious special characters
        import re
        # Allow common email characters: letters, numbers, dots, hyphens, underscores, plus signs
        if re.search(r'[<>|\\"\s]', local):
            return False

        # Additional validation: check for valid email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False

        return True

    @classmethod
    def create_project_notification(cls, user_email, action, project_name,
                                  project_id='', user_name='', extra_data=None):
        """
        Create project notification
        """
        if action == 'created':
            title = f"New project created: {project_name}"
            message = f"""A new project has been created successfully!

Project name: {project_name}
Project ID: {project_id}
Creation date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

You can now start adding code and files to the project."""

        elif action == 'deleted':
            title = f"Project deleted: {project_name}"
            message = f"""A project has been deleted!

Project name: {project_name}
Project ID: {project_id}
Deletion date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

All files and code related to this project have been deleted."""

        notification = cls(
            user_email=user_email,
            user_name=user_name,
            notification_type='PROJECT_CREATED' if action == 'created' else 'PROJECT_DELETED',
            title=title,
            message=message,
            related_id=project_id,
            related_type='project',
            priority='HIGH' if action == 'deleted' else 'MEDIUM',
            extra_data=extra_data
        )

        notification.send_email()
        return notification

    @classmethod
    def create_code_notification(cls, user_email, action, code_name, project_name,
                               code_id='', user_name='', extra_data=None):
        """
        Create code notification
        """
        if action == 'added':
            title = f"New code added: {code_name}"
            message = f"""A new code file has been added successfully!

File name: {code_name}
Project: {project_name}
File ID: {code_id}
Addition date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

You can now analyze the code and create documentation."""

        elif action == 'deleted':
            title = f"Code file deleted: {code_name}"
            message = f"""A code file has been deleted!

File name: {code_name}
Project: {project_name}
File ID: {code_id}
Deletion date: {timezone.now().strftime('%Y-%m-%d %H:%M')}"""

        else:
            title = f"Unknown action on code: {code_name}"
            message = f"""An action has been performed on the code file:

File name: {code_name}
Project: {project_name}
File ID: {code_id}
Action date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

Action type: {action}"""

        notification = cls(
            user_email=user_email,
            user_name=user_name,
            notification_type='CODE_ADDED' if action == 'added' else 'CODE_DELETED' if action == 'deleted' else 'CODE_UPDATED',
            title=title,
            message=message,
            related_id=code_id,
            related_type='code',
            priority='MEDIUM',
            extra_data=extra_data
        )

        notification.send_email()
        return notification

    @classmethod
    def create_documentation_notification(cls, user_email, file_name, file_type,
                                       project_name='', user_name='', extra_data=None):
        """
        Create documentation notification
        """
        title = f"Documentation file exported: {file_name}"
        message = f"""A documentation file has been exported successfully!

File name: {file_name}
File type: {file_type}
Project: {project_name or 'Not specified'}
Export date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

You can now download the file from the generated files section."""

        notification = cls(
            user_email=user_email,
            user_name=user_name,
            notification_type='DOCUMENTATION_EXPORTED',
            title=title,
            message=message,
            related_type='documentation',
            priority='LOW',
            extra_data=extra_data
        )

        notification.send_email()
        return notification

    @classmethod
    def create_user_notification(cls, user_email, action, user_name='', extra_data=None):
        """
        Create user notification
        """
        if action == 'registered':
            title = f"Welcome to AutoTest & DocGen"
            message = f"""Your account has been created successfully!

Welcome {user_name or 'to'} AutoTest & DocGen
Email: {user_email}
Registration date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

You can now start creating projects and analyzing code."""

        elif action == 'password_changed':
            title = "Password changed"
            message = f"""Your password has been changed successfully!

If you did not make this change, please contact us immediately
Email: {user_email}
Change date: {timezone.now().strftime('%Y-%m-%d %H:%M')}"""

        else:
            title = f"User action: {action}"
            message = f"""An action has been performed on your account:

User name: {user_name or 'User'}
Email: {user_email}
Action date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

Action type: {action}"""

        notification = cls(
            user_email=user_email,
            user_name=user_name,
            notification_type='USER_REGISTERED' if action == 'registered' else 'PASSWORD_CHANGED' if action == 'password_changed' else 'USER_ACTION',
            title=title,
            message=message,
            related_type='user',
            priority='HIGH' if action == 'password_changed' else 'MEDIUM',
            extra_data=extra_data
        )

        notification.send_email()
        return notification

    @classmethod
    def create_system_notification(cls, alert_type, message, user_email='',
                                 user_name='', extra_data=None):
        """
        Create system notification
        """
        title = f"System alert: {alert_type}"

        notification = cls(
            user_email=user_email or 'admin@example.com',  # default system email
            user_name=user_name or 'System Administrator',
            notification_type='SYSTEM_ALERT',
            title=title,
            message=message,
            priority='CRITICAL',
            extra_data=extra_data
        )

        notification.send_email()
        return notification


# Helper functions for integration with other systems
def send_project_notification(user_email, action, project_name, **kwargs):
    """
    Helper function to send project notification
    """
    return SimpleNotification.create_project_notification(
        user_email=user_email,
        action=action,
        project_name=project_name,
        **kwargs
    )


def send_code_notification(user_email, action, code_name, project_name, **kwargs):
    """
    Helper function to send code notification
    """
    return SimpleNotification.create_code_notification(
        user_email=user_email,
        action=action,
        code_name=code_name,
        project_name=project_name,
        **kwargs
    )


def send_documentation_notification(user_email, file_name, file_type, **kwargs):
    """
    Helper function to send documentation notification
    """
    return SimpleNotification.create_documentation_notification(
        user_email=user_email,
        file_name=file_name,
        file_type=file_type,
        **kwargs
    )


def send_user_notification(user_email, action, **kwargs):
    """
    Helper function to send user notification
    """
    return SimpleNotification.create_user_notification(
        user_email=user_email,
        action=action,
        **kwargs
    )


def send_system_alert(user_email, alert_type, message, **kwargs):
    """
    Helper function to send system alert
    """
    return SimpleNotification.create_system_notification(
        user_email=user_email,
        alert_type=alert_type,
        message=message,
        **kwargs
    )
