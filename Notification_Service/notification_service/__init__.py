"""
Notification Service Package
خدمة الإشعارات
"""

try:
    from .celery_app import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    celery_app = None
    __all__ = ()
