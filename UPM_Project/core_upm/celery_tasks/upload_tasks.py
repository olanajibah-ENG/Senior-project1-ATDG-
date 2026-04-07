"""
core_upm/celery_tasks/upload_tasks.py  ← جديد كلياً
=====================================
ليش هاد الملف موجود؟
    هو الـ "رسالة" اللي UPM بيبعثها لـ Redis.
    AI Celery worker يستقبل هاي الرسالة ويشتغل.

شو بيصير بالضبط؟
    1. UPM يستدعي process_upload_task.delay(...)
       → يحط الرسالة في Redis فوراً ويرجع task_id
    2. AI celery_worker يشوف الرسالة في Redis
       → يبعث HTTP request لنفسه داخلياً على /upload-folder/
       → يحفظ الملفات في GridFS + MongoDB
       → يحفظ في MySQL عبر callback لـ UPM
    3. الفرونت يقدر يتحقق من الحالة بـ task_id
"""

import logging
import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)

AI_UPLOAD_URL = 'http://ai_django_app:8000/api/analysis/upload-folder/'
UPM_MYSQL_CALLBACK_URL = 'http://upm_django_app:8000/api/upm/internal/upload-complete/'


@shared_task(
    bind=True,
    max_retries=3,           # يعيد المحاولة 3 مرات لو فشل
    default_retry_delay=60,  # ينتظر 60 ثانية بين كل محاولة
    name='upload_tasks.process_upload'
)
def process_upload_task(self, project_id, project_name, user_email, files_data):
    """
    الـ Task الرئيسي للرفع — بيشتغل في الخلفية.

    المعاملات:
        project_id   : UUID المشروع من MySQL
        project_name : اسم المشروع
        user_email   : بريد المستخدم
        files_data   : قائمة من {"filename": "...", "content": "...", "content_type": "..."}

    ليش files_data وما نبعت الملفات مباشرة؟
        Celery بيخزن الرسائل كـ JSON في Redis.
        الملفات الثنائية ما تنحفظ كـ JSON — لازم نحولها لـ base64 أو نبعث المحتوى كـ text.
        هنا بنبعث المحتوى كـ text لأن الملفات كود (text files).
    """
    task_id = self.request.id
    logger.info(f"[UPLOAD-TASK] Started — task:{task_id}, project:{project_id}, files:{len(files_data)}")

    try:
        # بناء الـ multipart files من البيانات المخزنة
        files_to_forward = []
        for file_info in files_data:
            filename = file_info['filename']
            content  = file_info['content'].encode('utf-8')
            ctype    = file_info.get('content_type', 'text/plain')
            files_to_forward.append(('files', (filename, content, ctype)))

        if not files_to_forward:
            logger.warning(f"[UPLOAD-TASK] No files to process — task:{task_id}")
            return {'status': 'skipped', 'reason': 'no files'}

        # إرسال الملفات لـ AI service
        logger.info(f"[UPLOAD-TASK] Sending {len(files_to_forward)} files to AI — task:{task_id}")
        ai_response = requests.post(
            AI_UPLOAD_URL,
            data={
                'project_name':   project_name,
                'user_email':     user_email,
                'upm_project_id': str(project_id),
            },
            files=files_to_forward,
            headers={'Host': 'localhost'},
            timeout=600  # 10 دقائق — بدون خوف من timeout لأنه في الخلفية
        )
        ai_response.raise_for_status()
        ai_data = ai_response.json()

        logger.info(
            f"[UPLOAD-TASK] AI done — task:{task_id}, "
            f"files:{ai_data.get('file_count', 0)}, version:{ai_data.get('version_number')}"
        )

        # إرسال نتيجة AI لـ UPM لحفظها في MySQL
        logger.info(f"[UPLOAD-TASK] Saving to MySQL — task:{task_id}")
        mysql_response = requests.post(
            UPM_MYSQL_CALLBACK_URL,
            json={
                'project_id': str(project_id),
                'ai_data':    ai_data,
                'task_id':    task_id,
            },
            headers={
                'Host':          'localhost',
                'X-Internal-Key': settings.INTERNAL_SERVICE_KEY,
            },
            timeout=60
        )
        mysql_response.raise_for_status()
        mysql_data = mysql_response.json()

        logger.info(f"[UPLOAD-TASK] Completed — task:{task_id}")
        return {
            'status':         'completed',
            'project_id':     str(project_id),
            'version_number': ai_data.get('version_number'),
            'file_count':     ai_data.get('file_count', 0),
            'mysql_saved':    mysql_data,
        }

    except requests.exceptions.ConnectionError as e:
        logger.error(f"[UPLOAD-TASK] Connection error — task:{task_id}: {e}")
        # يعيد المحاولة تلقائياً بعد 60 ثانية
        raise self.retry(exc=e)

    except requests.exceptions.Timeout as e:
        logger.error(f"[UPLOAD-TASK] Timeout — task:{task_id}: {e}")
        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"[UPLOAD-TASK] Failed — task:{task_id}: {e}")
        # لو استنفذ كل المحاولات → يسجل الفشل
        if self.request.retries >= self.max_retries:
            logger.critical(f"[UPLOAD-TASK] All retries exhausted — task:{task_id}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    name='upload_tasks.process_github_sync'
)
def process_github_sync_task(self, project_id, project_name, user_email, files_data, repo_id, new_sha):
    """
    Task لمزامنة GitHub — نفس فكرة process_upload_task لكن للـ GitHub sync والـ webhook.

    المعاملات الإضافية:
        repo_id : UUID الـ Repository في MySQL (لتحديث last_commit_sha بعد النجاح)
        new_sha : الـ SHA الجديد اللي رح نحفظه بعد نجاح المزامنة
    """
    task_id = self.request.id
    logger.info(
        f"[GITHUB-TASK] Started — task:{task_id}, project:{project_id}, "
        f"files:{len(files_data)}, sha:{new_sha[:7] if new_sha else 'N/A'}"
    )

    try:
        files_to_forward = []
        for file_info in files_data:
            filename = file_info['filename']
            content  = file_info['content'].encode('utf-8')
            ctype    = file_info.get('content_type', 'text/plain')
            files_to_forward.append(('files', (filename, content, ctype)))

        if not files_to_forward:
            logger.info(f"[GITHUB-TASK] No files changed — task:{task_id}")
            return {'status': 'no_changes'}

        logger.info(f"[GITHUB-TASK] Sending {len(files_to_forward)} files to AI — task:{task_id}")
        ai_response = requests.post(
            AI_UPLOAD_URL,
            data={
                'project_name':   project_name,
                'user_email':     user_email,
                'upm_project_id': str(project_id),
            },
            files=files_to_forward,
            headers={'Host': 'localhost'},
            timeout=600
        )
        ai_response.raise_for_status()
        ai_data = ai_response.json()

        # إرسال النتيجة لـ UPM لحفظها في MySQL + تحديث last_commit_sha
        mysql_response = requests.post(
            UPM_MYSQL_CALLBACK_URL,
            json={
                'project_id': str(project_id),
                'ai_data':    ai_data,
                'task_id':    task_id,
                'repo_id':    str(repo_id),
                'new_sha':    new_sha,
            },
            headers={
                'Host':           'localhost',
                'X-Internal-Key': settings.INTERNAL_SERVICE_KEY,
            },
            timeout=60
        )
        mysql_response.raise_for_status()

        logger.info(f"[GITHUB-TASK] Completed — task:{task_id}, sha:{new_sha[:7]}")
        return {
            'status':         'completed',
            'new_sha':        new_sha,
            'files_synced':   ai_data.get('file_count', 0),
            'version_number': ai_data.get('version_number'),
        }

    except requests.exceptions.ConnectionError as e:
        raise self.retry(exc=e)
    except requests.exceptions.Timeout as e:
        raise self.retry(exc=e)
    except Exception as e:
        logger.error(f"[GITHUB-TASK] Failed — task:{task_id}: {e}")
        if self.request.retries >= self.max_retries:
            logger.critical(f"[GITHUB-TASK] All retries exhausted — task:{task_id}")
        raise self.retry(exc=e)