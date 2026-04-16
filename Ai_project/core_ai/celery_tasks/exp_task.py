import logging
import traceback
from bson.objectid import ObjectId
from Ai_project.celery_app import app
from django.conf import settings
from core_ai.mongo_utils import get_mongo_db
from core_ai.ai_engine.orchestrator import DocumentationOrchestrator
from core_ai.models.ai_task import AITask
from core_ai.repository.ai_task import AITaskRepository
from core_ai.notification_utils import NotificationClient
from threading import Thread

logger = logging.getLogger(__name__)

def _trigger_evaluation_background(explanation_id: str):
    """Run evaluation in background thread after explanation is saved"""
    try:
        from core_ai.services.evaluation_service import ExplanationEvaluator
        evaluator = ExplanationEvaluator()
        evaluator.evaluate_explanation(explanation_id)
    except Exception as e:
        # Never raise — evaluation failure must not affect the main task
        print(f"[AUTO-EVAL] Failed for explanation {explanation_id}: {str(e)}")

def normalize_explanation_type(exp_type):
    """توحيد نوع الشرح إلى القيم القياسية"""
    if not exp_type: return 'high_level'
    t = str(exp_type).lower()
    if any(x in t for x in ['high', 'executive', 'business']): return 'high_level'
    if any(x in t for x in ['low', 'technical', 'detailed']): return 'low_level'
    return 'high_level'

@app.task(bind=True)
def generate_ai_explanation_task(self, analysis_id, exp_type, user_email=None):
    """توليد شرح AI بناءً على تحليل موجود مسبقاً"""
    normalized_exp_type = normalize_explanation_type(exp_type)
    is_valid_object_id = ObjectId.is_valid(analysis_id)
    # سجل تتبع المهمة
    task_analysis_id = ObjectId(analysis_id) if is_valid_object_id else str(analysis_id)
    task_model = AITask(task_id=self.request.id, analysis_id=task_analysis_id, 
                        exp_type=normalized_exp_type, status='processing')
    task_record = AITaskRepository(task_model)

    try:
        task_record.save()
        db = get_mongo_db()
        # Look in regular analysis results first
        analysis = None
        if is_valid_object_id:
            # البحث بـ ObjectId في نتائج التحليل العادية
            analysis = db[settings.ANALYSIS_RESULTS_COLLECTION].find_one({"_id": ObjectId(analysis_id)})
            # إذا لم يُوجد، ابحث في نتائج تحليل المشاريع
            if not analysis:
                analysis = db['project_analysis_results'].find_one({"_id": ObjectId(analysis_id)})
        else:
            # البحث بـ UUID (project_id) في نتائج تحليل المشاريع
            analysis = db['project_analysis_results'].find_one({"project_id": str(analysis_id)})
            if not analysis:
                # محاولة ثانية: البحث كـ string في _id
                analysis = db['project_analysis_results'].find_one({"_id": str(analysis_id)})

        if not analysis or analysis.get('status') not in ['COMPLETED', 'COMPLETED_WITH_ERRORS']:
            status = analysis.get('status') if analysis else 'NOT_FOUND'
            raise ValueError(f"Analysis record not found or not completed (Status: {status}).")

        # تشغيل الأوركستريتور
        orchestrator = DocumentationOrchestrator(analysis_id)
        content, explanation_id = orchestrator.get_or_generate_explanation(normalized_exp_type)
        
        result = {
            "status": "completed",
            "explanation_id": str(explanation_id),
            "type": normalized_exp_type,
            "content": content
        }

        task_record.update_status('completed', result=result)

        # Auto-trigger evaluation in background
        try:
            from core_ai.services.auto_trigger import trigger_evaluation_background
            trigger_evaluation_background(str(explanation_id))
        except Exception as eval_err:
            logger.warning(f"[AUTO-EVAL] Skipped: {eval_err}")
            
        if user_email:
            NotificationClient.send_custom_notification(
                user_email=user_email,
                title="تم توليد الشرح",
                message=f"شرح {normalized_exp_type} جاهز الآن.",
                notification_type="EXPLANATION_COMPLETED"
            )
        return result

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ [EXPLANATION] Failed: {error_msg}")
        task_record.update_status('failed', error=error_msg)
        if user_email:
            NotificationClient.send_system_alert(user_email=user_email, alert_type="error", message=error_msg)
        raise