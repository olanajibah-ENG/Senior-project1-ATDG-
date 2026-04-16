from celery import shared_task
from core_ai.mongo_utils import save_conflict_report, update_conflict_report
from core_ai.services.conflict_detection.orchestrator import ReportGenerator
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@shared_task
def analyze_conflict_task(project_id, analysis_type, analysis_a, analysis_b=None, explanation=None):
    logger.info(f"Task started for project {project_id}")

    # 1. إنشاء سجل مبدئي في MongoDB
    initial_data = {
        "project_id": project_id,
        "version_a": analysis_a.get("version"),
        "version_b": analysis_b.get("version") if analysis_b else None,
        "analysis_type": analysis_type,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    # حفظ والحصول على الـ ID
    report_id = save_conflict_report(initial_data)

    try:
        # 2. تشغيل التحليل
        if analysis_type == "code_vs_code":
            result = ReportGenerator.run_code_vs_code(analysis_a, analysis_b)
        elif analysis_type == "code_vs_doc":
            result = ReportGenerator.run_code_vs_doc(analysis_a, explanation)
        else:
            result = ReportGenerator.run_full_analysis(analysis_a, analysis_b, explanation)

        # 3. تجهيز بيانات التحديث
        update_data = {
            "structural_conflicts": [c.dict() for c in result.structural_conflicts],
            "semantic_conflicts": [c.dict() for c in result.semantic_conflicts],
            "doc_conflicts": [c.dict() for c in result.doc_conflicts],
            "summary": result.summary,
            "breaking_changes_count": result.breaking_changes_count,
            "compatibility_score": result.compatibility_score,
            "status": "completed"
        }
        
        # 4. تحديث السجل في MongoDB
        update_conflict_report(report_id, update_data)
        logger.info(f"Task completed for report {report_id}")
        return report_id

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        # تحديث الحالة للفشل
        update_conflict_report(report_id, {"status": "failed", "summary": str(e)})
        return str(e)