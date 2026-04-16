"""
upload_tasks.py ← معدّل
إصلاح: إضافة user_email في الـ data المُرسَل لـ AI
"""

import logging
import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)

AI_UPLOAD_URL        = 'http://ai_django_app:8000/api/analysis/upload-folder/'
UPM_MYSQL_CALLBACK_URL = 'http://upm_django_app:8000/api/upm/internal/upload-complete/'


def _build_files_to_forward(files_data):
    """يحول files_data لـ multipart list مناسب لـ requests.post"""
    result = []
    for file_info in files_data:
        filename = file_info['filename']
        is_zip   = file_info.get('is_zip', False)
        if is_zip:
            content = file_info['content'].encode('latin-1')
            result.append(('file', (filename, content, 'application/zip')))
        else:
            content = file_info['content'].encode('utf-8')
            ctype   = file_info.get('content_type', 'text/plain')
            result.append(('files', (filename, content, ctype)))
    return result


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='upload_tasks.process_upload'
)
def process_upload_task(self, project_id, project_name, user_email, files_data):
    task_id = self.request.id
    logger.info(f"[UPLOAD-TASK] Started — task:{task_id}, project:{project_id}, files:{len(files_data)}")

    try:
        files_to_forward = _build_files_to_forward(files_data)

        if not files_to_forward:
            logger.warning(f"[UPLOAD-TASK] No files — task:{task_id}")
            return {'status': 'skipped', 'reason': 'no files'}

        logger.info(f"[UPLOAD-TASK] Sending {len(files_to_forward)} files to AI — task:{task_id}")

        ai_response = requests.post(
            AI_UPLOAD_URL,
            data={
                'project_name':   project_name,
                'upm_project_id': str(project_id),
                'user_email':     user_email or '',   # ← كان ناقص
            },
            files=files_to_forward,
            headers={'Host': 'localhost'},
            timeout=600
        )

        # لو طلع error، نسجل التفاصيل قبل ما raise
        if not ai_response.ok:
            logger.error(
                f"[UPLOAD-TASK] AI returned {ai_response.status_code}: {ai_response.text[:500]}"
            )
        ai_response.raise_for_status()
        ai_data = ai_response.json()

        logger.info(
            f"[UPLOAD-TASK] AI done — files:{ai_data.get('file_count', 0)}, "
            f"version:{ai_data.get('version_number')}"
        )

        # callback لـ UPM لحفظ في MySQL
        mysql_response = requests.post(
            UPM_MYSQL_CALLBACK_URL,
            json={
                'project_id': str(project_id),
                'ai_data':    ai_data,
                'task_id':    task_id,
            },
            headers={
                'Host':           'localhost',
                'X-Internal-Key': settings.INTERNAL_SERVICE_KEY,
            },
            timeout=60
        )
        if not mysql_response.ok:
            logger.error(
                f"[UPLOAD-TASK] MySQL callback {mysql_response.status_code}: {mysql_response.text[:300]}"
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
        logger.error(f"[UPLOAD-TASK] Connection error: {e}")
        raise self.retry(exc=e)
    except requests.exceptions.Timeout as e:
        logger.error(f"[UPLOAD-TASK] Timeout: {e}")
        raise self.retry(exc=e)
    except Exception as e:
        logger.error(f"[UPLOAD-TASK] Failed: {e}")
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
    task_id = self.request.id
    logger.info(
        f"[GITHUB-TASK] Started — task:{task_id}, project:{project_id}, "
        f"files:{len(files_data)}, sha:{new_sha[:7] if new_sha else 'N/A'}"
    )

    try:
        files_to_forward = _build_files_to_forward(files_data)

        if not files_to_forward:
            logger.info(f"[GITHUB-TASK] No files — task:{task_id}")
            return {'status': 'no_changes'}

        ai_response = requests.post(
            AI_UPLOAD_URL,
            data={
                'project_name':   project_name,
                'upm_project_id': str(project_id),
                'user_email':     user_email or '',   # ← كان ناقص
            },
            files=files_to_forward,
            headers={'Host': 'localhost'},
            timeout=600
        )
        if not ai_response.ok:
            logger.error(f"[GITHUB-TASK] AI {ai_response.status_code}: {ai_response.text[:500]}")
        ai_response.raise_for_status()
        ai_data = ai_response.json()

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
        if not mysql_response.ok:
            logger.error(f"[GITHUB-TASK] MySQL {mysql_response.status_code}: {mysql_response.text[:300]}")
        mysql_response.raise_for_status()

        logger.info(f"[GITHUB-TASK] Completed — sha:{new_sha[:7]}")
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
        logger.error(f"[GITHUB-TASK] Failed: {e}")
        if self.request.retries >= self.max_retries:
            logger.critical(f"[GITHUB-TASK] All retries exhausted — task:{task_id}")
        raise self.retry(exc=e)