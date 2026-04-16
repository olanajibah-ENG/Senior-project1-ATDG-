import logging
import traceback
from datetime import datetime
from bson.objectid import ObjectId
from celery import shared_task
from django.conf import settings

from core_ai.mongo_utils import get_mongo_db, read_from_gridfs
from core_ai.language_processors.python_processor import PythonProcessor
from core_ai.language_processors.java_processor import JavaProcessor
from core_ai.services.project_analyzer import ProjectAnalyzer
from core_ai.models.codefile import CodeFile
from core_ai.models.analysis import AnalysisResult, AnalysisJob

logger = logging.getLogger(__name__)


@shared_task
def analyze_code_file_task(code_file_id_str):
    """تحليل الكود فقط - بدون توليد شرح منطقي"""
    task_id = analyze_code_file_task.request.id
    logger.info(f" [ANALYZE] Starting Task: {task_id} for File: {code_file_id_str}")

    db = get_mongo_db()
    if db is None:
        raise Exception("Database connection failed")

    code_files_collection = db[settings.CODE_FILES_COLLECTION]
    analysis_results_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]
    analysis_jobs_collection = db['analysis_jobs']

    code_file_id_obj = None
    try:
        code_file_id_obj = ObjectId(code_file_id_str)
        code_file_data = code_files_collection.find_one({"_id": code_file_id_obj})

        if not code_file_data:
            raise ValueError(f"Code file not found: {code_file_id_str}")

        code_file = CodeFile(**code_file_data)

        # ── جيب المحتوى من GridFS ──────────────────────────────────────────
        if not code_file.gridfs_id:
            raise ValueError(f"No GridFS ID found for file: {code_file_id_str}")

        logger.info(f" [ANALYZE] Reading content from GridFS: {code_file.gridfs_id}")
        code_content = read_from_gridfs(code_file.gridfs_id)
        logger.info(f" [ANALYZE] Content loaded, size: {len(code_content)} chars")

        # إنشاء AnalysisJob لتتبع تحليل الكود
        analysis_job = AnalysisJob(
            code_file_id=code_file_id_obj,
            status="STARTED",
            started_at=datetime.utcnow()
        )

        analysis_job_data = analysis_job.dict(by_alias=True, exclude_unset=True)
        if '_id' in analysis_job_data:
            del analysis_job_data['_id']

        analysis_jobs_collection.insert_one(analysis_job_data)
        logger.info(f" Created AnalysisJob for File: {code_file_id_str}")

        # تحديث الحالة
        code_files_collection.update_one(
            {"_id": code_file_id_obj},
            {"$set": {"analysis_status": "IN_PROGRESS"}}
        )

        # اختيار المعالج
        processor = PythonProcessor() if code_file.file_type == 'python' else JavaProcessor()

        # التحليل — نمرر المحتوى المجلوب من GridFS
        analyzer = ProjectAnalyzer(processor)
        analysis_result = analyzer.analyze_code(code_content)

        # إعداد النتيجة للحفظ
        result_instance = AnalysisResult(
            code_file_id=code_file_id_obj,
            analysis_started_at=datetime.utcnow(),
            analysis_completed_at=datetime.utcnow(),
            status="COMPLETED",
            ast_structure=analysis_result.get('ast_structure'),
            extracted_features=analysis_result.get('features_extracted'),
            dependencies=analysis_result.get('dependencies', []),
            dependency_graph=analysis_result.get('dependency_graph'),
            semantic_analysis_data=analysis_result.get('semantic_analysis_output'),
            class_diagram_data=analysis_result.get('class_diagram_data'),
        )

        result_data = result_instance.dict(by_alias=True, exclude_unset=True)
        if '_id' in result_data:
            del result_data['_id']

        inserted = analysis_results_collection.insert_one(result_data)
        analysis_id = str(inserted.inserted_id)

        # تحديث AnalysisJob بالنتيجة النهائية
        analysis_jobs_collection.update_one(
            {"code_file_id": code_file_id_obj},
            {"$set": {
                "status": "COMPLETED",
                "completed_at": datetime.utcnow()
            }}
        )

        # تحديث حالة الملف النهائية
        code_files_collection.update_one(
            {"_id": code_file_id_obj},
            {"$set": {
                "analysis_status": "COMPLETED",
                "analysis_id": ObjectId(analysis_id)
            }}
        )

        logger.info(f"✅ [ANALYZE] Completed Task: {task_id}")
        return analysis_id

    except Exception as e:
        logger.error(f"❌ [ANALYZE] Failed: {str(e)}")

        try:
            analysis_jobs_collection.update_one(
                {"code_file_id": code_file_id_obj},
                {"$set": {
                    "status": "FAILED",
                    "completed_at": datetime.utcnow(),
                    "error_message": str(e)
                }}
            )
        except:
            pass

        if code_file_id_obj:
            code_files_collection.update_one(
                {"_id": code_file_id_obj},
                {"$set": {"analysis_status": "FAILED"}}
            )
        raise


@shared_task
def reanalyze_code_file_task(code_file_id_str):
    """إعادة تحليل ملف كود موجود"""
    db = get_mongo_db()
    db[settings.ANALYSIS_RESULTS_COLLECTION].delete_many(
        {"code_file_id": ObjectId(code_file_id_str)}
    )
    return analyze_code_file_task(code_file_id_str)