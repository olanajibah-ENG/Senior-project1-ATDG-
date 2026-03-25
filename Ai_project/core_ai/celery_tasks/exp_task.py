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

logger = logging.getLogger(__name__)

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
    
    db = get_mongo_db()
    actual_analysis_id = None
    
    from bson.errors import InvalidId
    try:
        obj_id = ObjectId(analysis_id)
        # Check analysis_results
        if db[settings.ANALYSIS_RESULTS_COLLECTION].find_one({"_id": obj_id, "status": "COMPLETED"}):
            actual_analysis_id = obj_id
        # Check project_analysis_results by _id
        elif db['project_analysis_results'].find_one({"_id": obj_id, "status": "COMPLETED"}):
            actual_analysis_id = obj_id
    except InvalidId:
        pass
        
    if not actual_analysis_id:
        # Check project_analysis_results by project_id string
        p_doc = db['project_analysis_results'].find_one({"project_id": analysis_id, "status": "COMPLETED"})
        if p_doc:
            actual_analysis_id = p_doc['_id']
            
    if not actual_analysis_id:
        error_msg = "Analysis not found or not completed yet."
        # Generate dummy id to satisfy Pydantic validation if failed early
        task_model = AITask(task_id=self.request.id, analysis_id=ObjectId(), 
                            exp_type=normalized_exp_type, status='failed', error=error_msg)
        task_record = AITaskRepository(task_model)
        task_record.save()
        raise ValueError(error_msg)

    # سجل تتبع المهمة
    task_model = AITask(task_id=self.request.id, analysis_id=actual_analysis_id, 
                        exp_type=normalized_exp_type, status='processing')
    task_record = AITaskRepository(task_model)

    try:
        task_record.save()

        # تشغيل الأوركستريتور
        orchestrator = DocumentationOrchestrator(str(actual_analysis_id))
        content, explanation_id = orchestrator.get_or_generate_explanation(normalized_exp_type)
        
        result = {
            "status": "completed",
            "explanation_id": str(explanation_id),
            "type": normalized_exp_type,
            "content": content
        }

        task_record.update_status('completed', result=result)

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