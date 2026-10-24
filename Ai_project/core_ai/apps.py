from django.apps import AppConfig


class CoreAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_ai'

    def ready(self):
        try:
            from . import tasks  # noqa: F401
        except ImportError:
            pass  # تجاهل إذا لم يكن متوفراً
        
        # Import auto-trigger signals for evaluation
        try:
            from .services import auto_trigger  # noqa: F401
        except ImportError:
            pass  # تجاهل إذا لم يكن متوفراً