try:
    from Ai_project.celery_app import app as celery_app
except ImportError:
    celery_app = None

__all__ = ('celery_app',)
