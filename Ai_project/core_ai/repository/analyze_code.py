import traceback
import logging
from typing import Dict, Any
from core_ai.language_processors.python_processor import PythonProcessor
from core_ai.language_processors.java_processor import JavaProcessor
from core_ai.services.project_analyzer import ProjectAnalyzer
from core_ai.models.codefile import CodeFile
from core_ai.models.analysis import AnalysisResult
from core_ai.mongo_utils import get_mongo_db
from django.conf import settings
from datetime import datetime
from celery import shared_task
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)


@shared_task
def analyze_code_file_task(code_file_id_str):
    task_id = analyze_code_file_task.request.id
    
    logger.info(f"🔍 [ANALYZE] ==========================================")
    logger.info(f"🔍 [ANALYZE] Task ID: {task_id}")
    logger.info(f"🔍 [ANALYZE] Code File ID: {code_file_id_str}")
    logger.info(f"🔍 [ANALYZE] ==========================================")
    
    db = get_mongo_db()
    if db is None:
        logger.error("❌ [ANALYZE] Failed to connect to MongoDB")
        raise Exception("Database connection failed")
    
    code_files_collection = db[settings.CODE_FILES_COLLECTION]
    analysis_results_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]
    
    code_file_id_obj = None
    code_file = None
    
    try:
        # 1. تحويل code_file_id إلى ObjectId
        code_file_id_obj = ObjectId(code_file_id_str)
        
        # 2. جلب ملف الكود من قاعدة البيانات
        logger.info(f"📥 [ANALYZE] Fetching code file from database...")
        code_file_data = code_files_collection.find_one({"_id": code_file_id_obj})
        
        if not code_file_data:
            raise ValueError(f"Code file not found: {code_file_id_str}")
        
        code_file = CodeFile(**code_file_data)
        logger.info(f"✅ [ANALYZE] Code file loaded: {code_file.filename}")
        logger.info(f"📝 [ANALYZE] File type: {code_file.file_type}")
        logger.info(f"📝 [ANALYZE] File size: {len(code_file.content)} characters")
        
        # 3. تحديث حالة الملف إلى "في التحليل"
        code_files_collection.update_one(
            {"_id": code_file_id_obj},
            {"$set": {"analysis_status": "IN_PROGRESS"}}
        )
        
        # 4. اختيار المعالج المناسب بناءً على نوع الملف
        logger.info(f"🔧 [ANALYZE] Selecting language processor...")
        
        if code_file.file_type == 'python':
            processor = PythonProcessor()
            logger.info(f"✅ [ANALYZE] Using PythonProcessor")
        elif code_file.file_type == 'java':
            processor = JavaProcessor()
            logger.info(f"✅ [ANALYZE] Using JavaProcessor")
        else:
            raise ValueError(f"Unsupported file type: {code_file.file_type}")
        
        # 5. تحليل الكود باستخدام ProjectAnalyzer
        logger.info(f"🚀 [ANALYZE] Starting code analysis...")
        analyzer = ProjectAnalyzer(processor)
        analysis_result = analyzer.analyze_code(code_file.content)
        
        logger.info(f"✅ [ANALYZE] Code analysis completed successfully")
        logger.info(f"📊 [ANALYZE] Analysis results:")
        logger.info(f"  - AST Structure: {'✅' if analysis_result.get('ast_structure') else '❌'}")
        logger.info(f"  - Features: {'✅' if analysis_result.get('features_extracted') else '❌'}")
        logger.info(f"  - Dependencies: {len(analysis_result.get('dependencies', []))} found")
        logger.info(f"  - Class Diagram: {'✅' if analysis_result.get('class_diagram_data') else '❌'}")
        logger.info(f"  - Semantic Analysis: {'✅' if analysis_result.get('semantic_analysis_output') else '❌'}")
        
        # 6. إعداد البيانات للحفظ
        logger.info(f"💾 [ANALYZE] Preparing data for storage...")
        
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
        
        # 7. حفظ النتائج في قاعدة البيانات
        result_data = result_instance.dict(by_alias=True, exclude_unset=True)
        
        # إزالة _id إذا كان None لترك MongoDB يولده
        if '_id' in result_data and result_data['_id'] is None:
            del result_data['_id']
        
        logger.info(f"💾 [ANALYZE] Saving analysis results...")
        inserted = analysis_results_collection.insert_one(result_data)
        analysis_id = str(inserted.inserted_id)
        
        logger.info(f"✅ [ANALYZE] Analysis results saved with ID: {analysis_id}")
        
        # 8. تحديث حالة الملف إلى "مكتمل"
        code_files_collection.update_one(
            {"_id": code_file_id_obj},
            {"$set": {
                "analysis_status": "COMPLETED",
                "analysis_id": ObjectId(analysis_id)
            }}
        )
        
        logger.info(f"✅ [ANALYZE] Code file status updated to COMPLETED")
        logger.info(f"🎉 [ANALYZE] Analysis completed successfully!")
        logger.info(f"🎉 [ANALYZE] Analysis ID: {analysis_id}")
        logger.info(f"🔍 [ANALYZE] ==========================================")
        
        return analysis_id
        
    except ValueError as ve:
        error_message = f"Validation error: {str(ve)}"
        logger.error(f"❌ [ANALYZE] {error_message}")
        
        if code_file_id_obj:
            code_files_collection.update_one(
                {"_id": code_file_id_obj},
                {"$set": {"analysis_status": "FAILED"}}
            )
        
        raise
        
    except Exception as e:
        error_message = f"Analysis failed for CodeFile {code_file_id_str}: {e}"
        logger.error(f"❌ [ANALYZE] {error_message}")
        logger.error(f"❌ [ANALYZE] Traceback:")
        logger.error(traceback.format_exc())
        
        if code_file_id_obj:
            code_files_collection.update_one(
                {"_id": code_file_id_obj},
                {"$set": {"analysis_status": "FAILED"}}
            )
        
        raise


@shared_task
def reanalyze_code_file_task(code_file_id_str):
 
    logger.info(f"🔄 [REANALYZE] Starting reanalysis for: {code_file_id_str}")
    
    db = get_mongo_db()
    analysis_results_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]
    
    try:
        # 1. حذف التحليل السابق إن وجد
        code_file_id_obj = ObjectId(code_file_id_str)
        deleted = analysis_results_collection.delete_many({"code_file_id": code_file_id_obj})
        
        if deleted.deleted_count > 0:
            logger.info(f"🗑️ [REANALYZE] Deleted {deleted.deleted_count} old analysis results")
        
        # 2. تحليل جديد
        analysis_id = analyze_code_file_task(code_file_id_str)
        
        logger.info(f"✅ [REANALYZE] Reanalysis completed: {analysis_id}")
        return analysis_id
        
    except Exception as e:
        logger.error(f"❌ [REANALYZE] Reanalysis failed: {e}")
        raise


