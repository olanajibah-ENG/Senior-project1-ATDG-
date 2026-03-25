
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ai_project.settings')

app = Celery('Ai_project')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks([
    'core_ai.celery_tasks',
])

app.conf.imports = [
    'core_ai.celery_tasks.analyze_task',
    'core_ai.celery_tasks.exp_task',
    'core_ai.celery_tasks.analyze_project_task',
]
  

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')