import logging
from celery import shared_task
from django.conf import settings
from datetime import datetime
from core_ai.mongo_utils import get_mongo_db
from core_ai.celery_tasks.analyze_task import analyze_code_file_task
from core_ai.services.project_analysis_service import ProjectAnalysisService

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def analyze_project_task(self, project_id: str):
    db = get_mongo_db()
    if db is None:
        raise self.retry(exc=Exception("Database connection failed"), countdown=30, max_retries=3)

    # سجل البداية لمهمة التحليل
    record = db['project_analysis_results'].insert_one({
        "project_id": project_id,
        "status": "PENDING",
        "message": "Analysis queued",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    analysis_record_id = str(record.inserted_id)

    # ① جيبي كل ملفات المشروع
    all_files = list(
        db[settings.CODE_FILES_COLLECTION].find({
            "source_project_id": project_id
        })
    )

    if not all_files:
        db['project_analysis_results'].update_one(
            {"_id": record.inserted_id},
            {"$set": {"status": "FAILED", "message": "No files found", "updated_at": datetime.utcnow()}}
        )
        return {"error": "No files found"}

    # ② حلّلي الملفات الناقصة
    pending = [f for f in all_files if f.get('analysis_status') != 'COMPLETED']

    db['project_analysis_results'].update_one(
        {"_id": record.inserted_id},
        {"$set": {"status": "IN_PROGRESS", "message": "Analyzing code files", "updated_at": datetime.utcnow()}}
    )

    failed_files = []
    if pending:
        logger.info(f"[ANALYZE-PROJECT] Analyzing {len(pending)} pending files")
        tasks = []
        for f in pending:
            task = analyze_code_file_task.apply_async((str(f['_id']),), retry=False)
            tasks.append((f['_id'], task))

        for file_id, task in tasks:
            try:
                task.get(timeout=600)
            except Exception as e:
                logger.error(f"[ANALYZE-PROJECT] File task failed for {file_id}: {e}")
                failed_files.append(str(file_id))

    # ③ شغّلي الـ Service
    service = ProjectAnalysisService(project_id)
    project_files = service.get_project_files()

    if not project_files:
        db['project_analysis_results'].update_one(
            {"_id": record.inserted_id},
            {"$set": {"status": "FAILED", "message": "No completed files after analysis", "updated_at": datetime.utcnow()}}
        )
        return {"error": "No completed files after analysis"}

    graph_data = service.build_graph(project_files)
    contexts = service.build_contexts(project_files, graph_data['ordered'])
    analysis_ids = [f['analysis_id'] for f in project_files if f.get('analysis_id')]

    service.save_result(
        project_files=project_files,
        graph_data=graph_data,
        contexts=contexts,
        analysis_ids=analysis_ids,
        existing_record_id=analysis_record_id
    )

    if failed_files:
        service.set_analysis_status(analysis_record_id, "COMPLETED_WITH_ERRORS",
                                    f"Failed files: {len(failed_files)}")
    else:
        service.set_analysis_status(analysis_record_id, "COMPLETED", "Analysis completed successfully")

    logger.info(f"[ANALYZE-PROJECT] Done — project_id={project_id}, files={len(project_files)}")

    return {
        "project_id": project_id,
        "status": "COMPLETED_WITH_ERRORS" if failed_files else "COMPLETED",
        "total_files": len(project_files),
        "failed_files": failed_files,
        "ordered": graph_data['ordered'],
        "graph": graph_data['graph'],
        "analysis_ids": analysis_ids
    }