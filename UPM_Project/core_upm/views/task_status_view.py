"""
views/task_status_view.py  ← جديد كلياً
=========================
ليش هاد الملف موجود؟
    بعد ما الفرونت يرسل ملفات ويستقبل task_id،
    محتاج يعرف: هل خلص؟ هل فشل؟ شو النتيجة؟
    هاد الـ endpoint يجاوبه.

الفرونت يعمل polling:
    كل 3 ثواني يسأل عن الحالة حتى يشوف "completed" أو "failed"
"""

import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TaskStatusView(APIView):
    """
    GET /api/upm/tasks/<task_id>/

    يرجع حالة الـ Celery task.

    Response:
    لو شغال:
        {"task_id": "...", "status": "processing"}

    لو خلص:
        {
            "task_id"       : "...",
            "status"        : "completed",
            "version_number": 2,
            "file_count"    : 15,
            "mysql_saved"   : {"version": 2, "folders": 3, "artifacts": 15}
        }

    لو فشل:
        {"task_id": "...", "status": "failed", "error": "..."}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        result = AsyncResult(task_id)

        if result.state == 'PENDING':
            # الرسالة في Redis لسا ما أخذها أي worker
            return Response({
                "task_id": task_id,
                "status":  "pending",
                "message": "Task is waiting to be processed",
            })

        elif result.state == 'STARTED' or result.state == 'RETRY':
            # Worker أخذ الرسالة وبدأ يشتغل
            return Response({
                "task_id": task_id,
                "status":  "processing",
                "message": "Task is being processed",
            })

        elif result.state == 'SUCCESS':
            # خلص بنجاح
            task_result = result.result or {}
            return Response({
                "task_id":        task_id,
                "status":         "completed",
                "version_number": task_result.get('version_number'),
                "file_count":     task_result.get('file_count', 0),
                "mysql_saved":    task_result.get('mysql_saved', {}),
            })

        elif result.state == 'FAILURE':
            # فشل بعد كل المحاولات
            return Response({
                "task_id": task_id,
                "status":  "failed",
                "error":   str(result.result),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({
                "task_id": task_id,
                "status":  result.state.lower(),
            })