import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from bson.objectid import ObjectId
from core_ai.mongo_utils import get_mongo_db
from core_ai.celery_tasks.exp_task import generate_ai_explanation_task
from core_ai.models.ai_task import AITask
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


def get_safe_object_id(id_str):
    """
    دالة آمنة للتحقق من وتحويل ObjectId
    تمنع الأخطاء 500 عند إدخال قيم خاطئة
    """
    if id_str and ObjectId.is_valid(str(id_str).strip()):
        return ObjectId(str(id_str).strip())
    return None


@method_decorator(csrf_exempt, name='dispatch')
class AIExplanationViewSet(viewsets.ViewSet):
    """
    ViewSet لإدارة الشروحات المولدة من الذكاء الاصطناعي
    """
    permission_classes = [AllowAny]
    lookup_field = 'pk'
    lookup_value_regex = '[0-9a-fA-F]{24}'  # MongoDB ObjectId regex

    def initial(self, request, *args, **kwargs):
        """Override initial to add debugging"""
        logger.info(f"--- [ViewSet DEBUG] Initial called with URL: {request.path}")
        logger.info(f"--- [ViewSet DEBUG] Args: {args}")
        logger.info(f"--- [ViewSet DEBUG] Kwargs: {kwargs}")
        logger.info(f"--- [ViewSet DEBUG] Action: {getattr(self, 'action', 'unknown')}")
        return super().initial(request, *args, **kwargs)

    def list(self, request):
        """Display list of all explanations"""
        try:
            db = get_mongo_db()
            if db is None:
                return Response({
                    "error": "Database connection error",
                    "message": "Failed to connect to MongoDB database"
                }, status=500)

            collection_name = getattr(settings, 'AI_EXPLANATIONS_COLLECTION', 'ai_explanations')
            documents = list(db[collection_name].find(
                {},
                {
                    '_id': 1,
                    'explanation_type': 1,
                    'created_at': 1,
                    'analysis_id': 1
                }
            ).limit(100))  # حد أقصى 100 وثيقة

            for doc in documents:
                doc['_id'] = str(doc['_id'])
                if 'analysis_id' in doc and doc['analysis_id']:
                    doc['analysis_id'] = str(doc['analysis_id'])

            return Response(documents)

        except Exception as e:
            logger.error(f"--- [AIExplanationViewSet.list] Error: {str(e)} ---")
            return Response({
                "error": "System error",
                "message": f"An error occurred while fetching explanations list: {str(e)}"
            }, status=500)

    @action(detail=False, methods=['post'], url_path='generate-explanation')
    def generate_explanation(self, request):
        """
        توليد شرح جديد باستخدام الذكاء الاصطناعي
        """
        # ✅ التحقق المسبق من analysis_id
        raw_analysis_id = request.data.get('analysis_id')
        if not raw_analysis_id:
            return Response({
                "error": "Missing analysis_id",
                "message": "analysis_id is required"
            }, status=400)
            
        analysis_id = get_safe_object_id(raw_analysis_id)
        if not analysis_id:
            # Assume it's a project UUID string
            analysis_id_str = str(raw_analysis_id).strip()
        else:
            analysis_id_str = str(analysis_id)
        
        # ✅ محاولة الحصول على exp_type من مصادر متعددة
        exp_type = request.data.get('type', '').strip() if request.data.get('type') else None

        if not exp_type:
            exp_type = request.data.get('exp_type', '').strip() if request.data.get('exp_type') else None
            
        if not exp_type:
            exp_type = request.data.get('explanation_level', '').strip() if request.data.get('explanation_level') else None
            
        logger.info(f"🔍 [GenerateExplanation] DEBUG - Full request data: {request.data}")
        logger.info(f"🔍 [GenerateExplanation] DEBUG - analysis_id: {analysis_id_str}")
        logger.info(f"🔍 [GenerateExplanation] DEBUG - exp_type BEFORE normalization: '{exp_type}'")
        
        # ============================================================
        # ✅ توحيد exp_type - دعم جميع الصيغ المحتملة
        # ============================================================
        if exp_type:
            # Normalize explanation type - support all variations
            exp_type_lower = str(exp_type).strip().lower()
            
            # Define all possible variations
            # Define all possible variations
            high_level_variations = ['high', 'high_level', 'executive', 'business', 'high-level', 'high level']
            low_level_variations = ['low', 'low_level', 'technical', 'detailed', 'low-level', 'low level']

            # Determine the actual type with EXACT matching
            is_high_level = False
            is_low_level = False

            # Check for high_level first (priority)
            for variant in high_level_variations:
                if (exp_type_lower == variant) or (exp_type_lower.startswith(variant + '_')) or (exp_type_lower.endswith('_' + variant)):
                    is_high_level = True
                    break

            # Only check low_level if not high_level
            if not is_high_level:
                for variant in low_level_variations:
                    if (exp_type_lower == variant) or (exp_type_lower.startswith(variant + '_')) or (exp_type_lower.endswith('_' + variant)):
                        is_low_level = True
                        break

            # Assign normalized value
            if is_high_level:
                exp_type = 'high_level'
            elif is_low_level:
                exp_type = 'low_level'
            else:
                # Default to high_level if unknown
                exp_type = 'high_level'

            logger.info(f"🔍 [GenerateExplanation] DEBUG - exp_type AFTER normalization: '{exp_type}'")
                    # ============================================================
        # ✅ نهاية التوحيد
        # ============================================================
            
        if not exp_type:
            return Response({
                "error": "type is required",
                "message": "Please provide type, exp_type, or explanation_level",
                "received_data": str(request.data)
            }, status=400)

        try:
            logger.info(f"--- [GenerateExplanation] Starting async task for analysis_id: {analysis_id_str}, type: {exp_type} ---")

            # ✅ استدعاء المهمة
            task = generate_ai_explanation_task.delay(analysis_id_str, exp_type)

            logger.info(f"--- [GenerateExplanation] Task started with ID: {task.id} ---")

            return Response({
                "task_id": task.id,
                "status": "processing",
                "message": "Explanation generation started. Please check status later.",
                "analysis_id": analysis_id_str,
                "type": exp_type
            })

        except Exception as e:
            import traceback
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            logger.error(f"--- [GenerateExplanation] Error starting task for analysis_id: {analysis_id_str}, type: {exp_type} ---")
            logger.error(f"--- [GenerateExplanation] Error message: {error_msg} ---")
            logger.error(f"--- [GenerateExplanation] Traceback: {error_traceback} ---")

            return Response({
                "error": "Failed to start explanation generation",
                "message": error_msg,
                "details": error_traceback if settings.DEBUG else "Enable DEBUG mode for full traceback"
            }, status=500)

    @action(detail=False, methods=['get'], url_path='task-status')
    def get_task_status(self, request):
        """
        التحقق من حالة مهمة توليد الشرح
        URL: /api/analysis/ai-explanations/task-status/?task_id={task_id}
        """
        task_id = request.GET.get('task_id')

        if not task_id:
            return Response({"error": "task_id is required"}, status=400)

        try:
            # ✅ محاولة الحصول على المهمة من قاعدة البيانات أولاً
            task_record = AITask.get_by_task_id(task_id)

            if task_record:
                response_data = {
                    "task_id": task_id,
                    "status": task_record.status,
                    "analysis_id": str(task_record.analysis_id),  # Convert ObjectId to string
                    "exp_type": task_record.exp_type,
                    "created_at": task_record.created_at.isoformat() if task_record.created_at else None,
                }

                if task_record.status == "processing":
                    response_data.update({
                        "message": "Processing request...",
                        "progress": 50
                    })
                elif task_record.status == "completed":
                    response_data.update({
                        "message": "Task completed successfully",
                        "progress": 100,
                        "result": task_record.result,
                        "completed_at": task_record.completed_at.isoformat() if task_record.completed_at else None
                    })
                elif task_record.status == "failed":
                    response_data.update({
                        "message": "Task failed",
                        "progress": 0,
                        "error": task_record.error,
                        "completed_at": task_record.completed_at.isoformat() if task_record.completed_at else None
                    })
                else:
                    response_data.update({
                        "message": f"Task status: {task_record.status}",
                        "progress": 0
                    })

                return Response(response_data)

            # ✅ إذا لم يكن موجوداً في قاعدة البيانات، جرب Celery
            result = AsyncResult(task_id)

            response_data = {
                "task_id": task_id,
                "status": result.status,
            }

            if result.state == "PENDING":
                response_data.update({
                    "message": "Task is pending execution",
                    "progress": 0
                })
            elif result.state == "PROGRESS":
                response_data.update({
                    "message": "Processing request...",
                    "progress": getattr(result.info, 'progress', 50) if result.info else 50
                })
            elif result.state == "SUCCESS":
                response_data.update({
                    "message": "Task completed successfully",
                    "progress": 100,
                    "result": result.result
                })
            elif result.state == "FAILURE":
                response_data.update({
                    "message": "Task failed",
                    "progress": 0,
                    "error": str(result.info) if result.info else "Unknown error"
                })
            else:
                response_data.update({
                    "message": f"Unknown status: {result.state}",
                    "progress": 0
                })

            return Response(response_data)

        except Exception as e:
            logger.error(f"--- [TaskStatus] Error checking task {task_id}: {str(e)} ---")
            return Response({
                "error": "Failed to check task status",
                "message": str(e)
            }, status=500)

    @action(detail=False, methods=['get'], url_path='analysis-tasks')
    def get_analysis_tasks(self, request):
        """
        الحصول على جميع المهام الخاصة بتحليل معين
        URL: /api/analysis/ai-explanations/analysis-tasks/?analysis_id={analysis_id}
        """
        analysis_id = request.GET.get('analysis_id')

        if not analysis_id:
            return Response({"error": "analysis_id is required"}, status=400)

        # ✅ استخدام get_safe_object_id للتحقق الآمن
        analysis_id_obj = get_safe_object_id(analysis_id)
        if not analysis_id_obj:
            return Response({"error": "Invalid analysis_id format"}, status=400)

        try:
            # ✅ استخدام analysis_id كـ string للتوافق
            tasks = AITask.get_user_tasks(analysis_id=analysis_id, limit=20)

            tasks_data = []
            for task in tasks:
                task_data = {
                    "task_id": task.task_id,
                    "analysis_id": str(task.analysis_id),  # Convert ObjectId to string
                    "exp_type": task.exp_type,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                }

                if task.result:
                    task_data["result"] = task.result
                if task.error:
                    task_data["error"] = task.error

                tasks_data.append(task_data)

            return Response({
                "analysis_id": analysis_id,
                "tasks": tasks_data,
                "total": len(tasks_data)
            })

        except Exception as e:
            logger.error(f"--- [AnalysisTasks] Error getting tasks for analysis {analysis_id}: {str(e)} ---")
            return Response({
                "error": "Failed to get analysis tasks",
                "message": str(e)
            }, status=500)

    @action(detail=False, methods=['get'], url_path='export-legacy')
    def export_file_legacy(self, request):
        """
        دعم الرابط القديم للتوافق الخلفي
        URL: /api/analysis/ai-explanations/export-legacy/?id={ID}&format=pdf
        """
        logger.info("--- [ExportFileLegacy] Started ---")

        try:
            # ✅ استخدام get_safe_object_id للتحقق الآمن
            explanation_id = get_safe_object_id(request.GET.get('id'))
            if not explanation_id:
                logger.warning("--- [ExportFileLegacy] Missing or invalid ID parameter ---")
                return Response({
                    "error": "Invalid explanation ID",
                    "message": "Explanation ID must be a valid MongoDB ObjectId"
                }, status=400)

            format_type = request.GET.get('format', 'md').lower()
            if format_type not in ['pdf', 'md']:
                logger.warning(f"--- [ExportFileLegacy] Unsupported format: {format_type} ---")
                return Response({
                    "error": "Unsupported file format",
                    "message": "Supported formats are: pdf, md"
                }, status=400)

            logger.info(f"--- [ExportFileLegacy] Processing ID: {str(explanation_id)}, Format: {format_type} ---")

            from .export_views import handle_export_request
            return handle_export_request(str(explanation_id), format_type)

        except Exception as e:
            logger.error(f"--- [ExportFileLegacy] Unexpected error: {str(e)} ---")
            return Response({
                "error": "Unexpected error",
                "message": "An unexpected error occurred in the system"
            }, status=500)