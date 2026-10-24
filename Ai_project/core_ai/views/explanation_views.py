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
    if not id_str:
        return None
    
    clean_id = str(id_str).strip()
    if ObjectId.is_valid(clean_id):
        return ObjectId(clean_id)
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

    @action(detail=False, methods=['get'], url_path='by-analysis',
            permission_classes=[AllowAny], authentication_classes=[])
    def get_by_analysis(self, request):
        """
        جلب الشرح الكامل (مع content) بالـ analysis_id و type.
        URL: /api/analysis/ai-explanations/by-analysis/?analysis_id={ID}&type=high_level
        """
        from bson import ObjectId
        raw_id   = request.GET.get('analysis_id', '').strip()
        exp_type = request.GET.get('type', 'high_level').strip()

        if not raw_id:
            return Response({"error": "analysis_id is required"}, status=400)

        try:
            db = get_mongo_db()
            if db is None:
                return Response({"error": "Database connection error"}, status=500)

            collection = db[getattr(settings, 'AI_EXPLANATIONS_COLLECTION', 'ai_explanations')]

            # حاول بـ ObjectId أولاً
            query_ids = [raw_id]
            if ObjectId.is_valid(raw_id):
                query_ids.append(ObjectId(raw_id))

            doc = None
            for qid in query_ids:
                doc = collection.find_one({
                    "analysis_id": qid,
                    "$or": [{"explanation_type": exp_type}, {"exp_type": exp_type}]
                })
                if doc:
                    break

            if not doc:
                return Response({
                    "error": "Explanation not found",
                    "message": f"No {exp_type} explanation found for analysis_id={raw_id}"
                }, status=404)

            # تحويل ObjectIds لـ strings
            doc['_id']         = str(doc['_id'])
            doc['analysis_id'] = str(doc.get('analysis_id', ''))

            return Response(doc)

        except Exception as e:
            logger.error(f"--- [GetByAnalysis] Error: {e} ---")
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'], url_path='generate-explanation')
    def generate_explanation(self, request):
        """
        توليد شرح جديد باستخدام الذكاء الاصطناعي
        """
        # ✅ التحقق المسبق من analysis_id باستخدام get_safe_object_id
        raw_analysis_id = request.data.get('analysis_id')
        if not raw_analysis_id:
            return Response({
                "error": "analysis_id is required"
            }, status=400)

        raw_analysis_id = str(raw_analysis_id).strip()

        # تحديد نوع الـ ID: ObjectId (ملف) أم UUID (مشروع)
        import re
        uuid_regex = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
        is_project_uuid = uuid_regex.match(raw_analysis_id) is not None

        if is_project_uuid:
            # UUID مشروع: تحقق من وجود تحليل للمشروع
            try:
                db = get_mongo_db()
                project_res = db['project_analysis_results'].find_one(
                    {"project_id": raw_analysis_id},
                    sort=[("created_at", -1)]
                )
                if not project_res:
                    return Response({
                        "error": "Project analysis not found",
                        "message": "Please run project analysis first using /api/analysis/analyze-project/"
                    }, status=404)
                # ✅ نُبقي على الـ UUID الأصلي ونرسله مباشرة للـ task
                analysis_id_str = raw_analysis_id
                logger.info(f"--- [GenerateExplanation] Project UUID confirmed: {analysis_id_str} ---")
            except Exception as e:
                logger.error(f"Error checking project UUID: {str(e)}")
                return Response({"error": f"Database error: {str(e)}"}, status=500)

        elif get_safe_object_id(raw_analysis_id):
            # ObjectId عادي (ملف واحد)
            analysis_id_str = str(get_safe_object_id(raw_analysis_id))
            logger.info(f"--- [GenerateExplanation] File ObjectId confirmed: {analysis_id_str} ---")
        else:
            return Response({
                "error": "Invalid analysis_id format",
                "message": "analysis_id must be a valid MongoDB ObjectId (24-char hex) or a Project UUID (8-4-4-4-12 format)"
            }, status=400)
        
        # ✅ محاولة الحصول على exp_type من مصادر متعددة
        exp_type = request.data.get('type', '').strip() if request.data.get('type') else None

        if not exp_type:
            exp_type = request.data.get('exp_type', '').strip() if request.data.get('exp_type') else None
            
        if not exp_type:
            exp_type = request.data.get('explanation_level', '').strip() if request.data.get('explanation_level') else None
            
        print(f"!!! generate_explanation CALLED with analysis_id: {analysis_id_str} !!!")
        logger.info(f"--- [GenerateExplanation] DEBUG - Full request data: {request.data}")
        logger.info(f"--- [GenerateExplanation] DEBUG - analysis_id: {analysis_id_str}")
        logger.info(f"--- [GenerateExplanation] DEBUG - exp_type BEFORE normalization: '{exp_type}'")
        
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

    @action(detail=False, methods=['get'], url_path='export-legacy',
            permission_classes=[AllowAny], authentication_classes=[])
    def export_file_legacy(self, request):
        """
        دعم الرابط القديم للتوافق الخلفي
        URL: /api/analysis/ai-explanations/export-legacy/?id={ID}&format=pdf|md|html|xml&type=high_level|low_level
        """
        logger.info("--- [ExportFileLegacy] Started ---")

        try:
            raw_id = request.GET.get('id', '').strip()
            if not raw_id:
                return Response({"error": "id parameter is required"}, status=400)

            format_type = request.GET.get('format', 'md').lower()
            # normalize markdown → md
            if format_type == 'markdown':
                format_type = 'md'
            if format_type not in ['pdf', 'md', 'html', 'xml']:
                return Response({
                    "error": "Unsupported format",
                    "message": "Supported formats: pdf, md, html, xml"
                }, status=400)

            exp_type_raw = request.GET.get('type', 'high_level').lower()
            high_vars = ['high', 'high_level', 'executive', 'business']
            low_vars  = ['low',  'low_level',  'technical', 'detailed']
            if any(v in exp_type_raw for v in high_vars):
                exp_type = 'high_level'
            elif any(v in exp_type_raw for v in low_vars):
                exp_type = 'low_level'
            else:
                exp_type = 'high_level'

            mode = request.GET.get('mode', 'download')

            logger.info(f"--- [ExportFileLegacy] id={raw_id}, format={format_type}, type={exp_type}, mode={mode} ---")

            from .export_views import handle_export_with_auto_generation
            return handle_export_with_auto_generation(raw_id, exp_type, format_type, mode=mode)

        except Exception as e:
            logger.error(f"--- [ExportFileLegacy] Unexpected error: {str(e)} ---")
            return Response({"error": "Unexpected error", "message": str(e)}, status=500)