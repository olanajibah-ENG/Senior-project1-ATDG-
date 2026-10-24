"""
UPM_Project/UPM_Project/celery_app.py  ← جديد كلياً
======================================
ليش هاد الملف موجود؟
    Celery يحتاج نقطة دخول تعرّفه على الـ Django settings وتجمع كل الـ tasks.
    بدونه UPM ما يقدر يبعث أي رسالة للـ Redis.

شو بيعمل؟
    يهيئ Celery لـ UPM ويربطه بالـ Redis المشترك.
    autodiscover_tasks() → يدور تلقائياً على أي ملف اسمه tasks.py في كل app.
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UPM_Project.settings')

app = Celery('UPM_Project')

# يقرأ إعدادات Celery من settings.py (الأسطر اللي تبدأ بـ CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# يدور تلقائياً على كل ملف tasks.py في كل app
app.autodiscover_tasks()