"""
export_views.py  ← معدّل
===============
التغييرات عن النسخة القديمة:
    1. أُضيف دعم format=html  → HTMLGenerator
    2. أُضيف دعم format=xml   → XMLGenerator
    3. export_doc() و handle_export_with_auto_generation() يدعمان الـ formats الأربعة
    4. download_generated_file() يعرف content-type لـ html و xml
    5. لا شي اتحذف — كل الكود القديم شغّال كما هو
"""

import logging
import re
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from bson.objectid import ObjectId
from core_ai.mongo_utils import get_mongo_db
from core_ai.ai_engine.doc.markdown import MarkdownGenerator
from core_ai.ai_engine.doc.pdf import PDFGenerator
from core_ai.ai_engine.doc.html_generator import HTMLGenerator
from core_ai.ai_engine.doc.xml_generator import XMLGenerator
from core_ai.notification_utils import NotificationClient
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

logger = logging.getLogger(__name__)

# ── الـ formats المدعومة ────────────────────────────────────────────────────
SUPPORTED_FORMATS = ['pdf', 'markdown', 'md', 'html', 'xml']

FORMAT_CONTENT_TYPE = {
    'pdf':      'application/pdf',
    'md':       'text/markdown',
    'markdown': 'text/markdown',
    'html':     'text/html; charset=utf-8',
    'xml':      'application/xml; charset=utf-8',
}

FORMAT_EXTENSION = {
    'pdf':      '.pdf',
    'md':       '.md',
    'markdown': '.md',
    'html':     '.html',
    'xml':      '.xml',
}

FORMAT_DB_TYPE = {
    'pdf':      'pdf',
    'md':       'markdown',
    'markdown': 'markdown',
    'html':     'html',
    'xml':      'xml',
}


def slugify(value):
    if not value:
        return "file"
    value = str(value)
    value = re.sub(r'[/\\:*?"<>|]', '', value)
    value = re.sub(r'\s+', '_', value.strip())
    value = re.sub(r'[-_.]+', '_', value)
    value = value.strip('-_')
    return value if value else "file"


try:
    from core_ai.celery_tasks.exp_task import generate_ai_explanation_task
    CELERY_AVAILABLE = True
except Exception as e:
    logger.warning(f"Celery not available: {e}")
    CELERY_AVAILABLE = False
    generate_ai_explanation_task = None


def _build_generator(format_type: str):
    """
    يرجع الـ generator المناسب حسب الـ format.
    جديد: يدعم html و xml.
    """
    if format_type == 'pdf':
        return PDFGenerator()
    elif format_type == 'html':
        return HTMLGenerator()
    elif format_type == 'xml':
        return XMLGenerator()
    else:
        return MarkdownGenerator()


def _build_filename(data: dict, format_type: str, analysis_id: str) -> str:
    """يبني اسم الملف المناسب بالامتداد الصحيح."""
    original = data.get('filename', '')
    if not original:
        match = re.search(r'File[:\s]+([^\s\n]+)', str(data.get('content', '')))
        if match:
            original = match.group(1).strip()

    safe_name      = slugify(original) if original else "technical_report"
    safe_type      = slugify(data.get('explanation_type', 'doc'))
    safe_id        = slugify(analysis_id[:8])
    base           = f"{safe_name}_{safe_type}_{safe_id}"
    base           = re.sub(r'\.[^.]+$', '', base)  # احذف أي امتداد موجود
    ext            = FORMAT_EXTENSION.get(format_type, '.txt')
    return f"{base}{ext}"


def handle_export_with_auto_generation(analysis_id, explanation_type, format_type, image_url=None, user_email=None, mode='display'):
    """
    نقطة الدخول الموحدة — تدعم الآن: pdf, md, html, xml
    """
    logger.info(f"[ExportHandler] analysis_id:{analysis_id}, type:{explanation_type}, format:{format_type}")

    try:
        db = get_mongo_db()
        if db is None:
            return JsonResponse({"error": "Database connection error"}, status=500)

        collection_name = getattr(settings, 'AI_EXPLANATIONS_COLLECTION', 'ai_explanations')

        try:
            analysis_obj_id = ObjectId(analysis_id) if ObjectId.is_valid(analysis_id) else analysis_id
            # 1. تحقق إذا كان project_id (UUID)
            p_doc = db['project_analysis_results'].find_one({"project_id": str(analysis_id)})
            if p_doc:
                analysis_obj_id = p_doc['_id']
            else:
                # 2. fallback: ابحث عن analysis_result بالـ code_file_id
                if ObjectId.is_valid(str(analysis_id)):
                    ar = db[getattr(settings, 'ANALYSIS_RESULTS_COLLECTION', 'analysis_results')].find_one(
                        {"code_file_id": ObjectId(str(analysis_id))}
                    )
                    if ar:
                        logger.info(f"[ExportHandler] Resolved file_id {analysis_id} → analysis_id {ar['_id']}")
                        analysis_obj_id = ar['_id']
        except Exception as e:
            logger.warning(f"[ExportHandler] ID resolution error: {e}")
            analysis_obj_id = analysis_id

        # البحث عن الشرح — نفس منطق البحث القديم
        data = db[collection_name].find_one({
            "analysis_id": analysis_obj_id,
            "explanation_type": explanation_type
        })

        if data:
            data = _normalize_ids(data)

        if not data:
            data = db[collection_name].find_one({
                "analysis_id": analysis_obj_id,
                "exp_type": explanation_type
            })
            if data:
                data = _normalize_ids(data)

        if not data:
            tasks_collection = getattr(settings, 'AI_TASKS_COLLECTION', 'ai_tasks')
            task_data = db[tasks_collection].find_one({
                "analysis_id": analysis_obj_id,
                "exp_type": explanation_type,
                "status": "completed"
            })
            if task_data and isinstance(task_data, dict) and task_data.get('result', {}).get('content'):
                data = {
                    '_id': task_data.get('result', {}).get('explanation_id', 'temp_id'),
                    'content': task_data['result']['content'],
                    'exp_type': explanation_type,
                    'analysis_id': analysis_obj_id,
                    'created_at': task_data.get('created_at')
                }
            else:
                analysis_collection = getattr(settings, 'ANALYSIS_RESULTS_COLLECTION', 'analysis_results')
                analysis_data = db[analysis_collection].find_one({
                    "_id": ObjectId(analysis_id) if ObjectId.is_valid(analysis_id) else analysis_id
                })
                if not analysis_data:
                    p_doc = (
                        db['project_analysis_results'].find_one({"project_id": str(analysis_id)}) or
                        db['project_analysis_results'].find_one({"_id": ObjectId(analysis_id) if ObjectId.is_valid(analysis_id) else analysis_id})
                    )
                    if p_doc:
                        analysis_data = p_doc
                if not analysis_data:
                    return JsonResponse({
                        "error": "Analysis not found",
                        "message": f"No analysis found with ID '{analysis_id}'. Code must be analyzed first."
                    }, status=404)

                if not CELERY_AVAILABLE or generate_ai_explanation_task is None:
                    return JsonResponse({
                        "error": "Generation system unavailable",
                        "message": "Celery system is currently unavailable."
                    }, status=503)

                try:
                    task = generate_ai_explanation_task.delay(analysis_id, explanation_type)
                    return JsonResponse({
                        "status": "generating",
                        "message": "Generating requested explanation. Please wait...",
                        "task_id": task.id,
                        "analysis_id": analysis_id,
                        "explanation_type": explanation_type,
                        "estimated_time": "30-60 seconds"
                    }, status=202)
                except Exception as e:
                    return JsonResponse({
                        "error": "Failed to start generation",
                        "message": str(e)
                    }, status=503)

        if not data.get('content'):
            return JsonResponse({"error": "Empty content", "message": "Explanation exists but content is empty"}, status=404)

        if image_url:
            data['image_url'] = image_url

        # ── توليد الملف ───────────────────────────────────────────────────────
        try:
            generator = _build_generator(format_type)
            filename  = _build_filename(data, format_type, analysis_id)

            try:
                file_content = generator.generate(data)
            except Exception as gen_error:
                logger.error(f"[ExportHandler] Generation failed: {gen_error}")
                # fallback لـ PDF → Markdown
                if format_type == 'pdf':
                    logger.info("[ExportHandler] PDF failed — falling back to Markdown")
                    format_type  = 'md'
                    generator    = MarkdownGenerator()
                    file_content = generator.generate(data)
                    filename     = filename.replace('.pdf', '.md')
                else:
                    raise

            if not file_content:
                return JsonResponse({"error": "File generation failed"}, status=500)

            # حفظ الملف في MongoDB
            _save_generated_file(db, data, file_content, filename, format_type, analysis_id)

            # إشعار
            if user_email:
                try:
                    NotificationClient.send_documentation_notification(
                        user_email=user_email,
                        file_name=filename,
                        file_type=format_type,
                        project_name="analysis code",
                        user_name=""
                    )
                except Exception as e:
                    logger.warning(f"Notification failed: {e}")

            # الرد
            if mode == 'display':
                # لـ xml و html — نرجع المحتوى الفعلي بـ content-type الصح
                # لأن الفرونت بيحاول يعرضهم مباشرة
                if format_type in ('xml', 'html'):
                    if isinstance(file_content, str):
                        file_content = file_content.encode('utf-8')
                    content_type = FORMAT_CONTENT_TYPE.get(format_type, 'application/octet-stream')
                    response = HttpResponse(file_content, content_type=content_type)
                    response['Content-Disposition'] = f'inline; filename="{filename}"'
                    return response
                # لـ md و pdf — نرجع JSON مع المحتوى النصي
                return JsonResponse({
                    "status":   "success",
                    "format":   format_type,
                    "content":  data.get('content', ''),
                    "filename": filename
                })
            else:
                if isinstance(file_content, str):
                    file_content = file_content.encode('utf-8')
                content_type = FORMAT_CONTENT_TYPE.get(format_type, 'application/octet-stream')
                from urllib.parse import quote
                response = HttpResponse(file_content, content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
                response['Content-Length']  = str(len(file_content))
                response['Cache-Control']   = 'no-cache, no-store, must-revalidate'
                response['Accept-Ranges']   = 'bytes'
                return response

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[ExportHandler] Error: {error_msg}")
            if any(k in error_msg.lower() for k in ['cairo', 'weasyprint', 'pdf']):
                return JsonResponse({
                    "error": "PDF not supported",
                    "message": "PDF generation unavailable. Use format=md, format=html, or format=xml instead."
                }, status=503)
            return JsonResponse({"error": "File generation error", "message": error_msg}, status=500)

    except Exception as e:
        logger.error(f"[ExportHandler] System error: {e}")
        return JsonResponse({"error": "System error", "message": str(e)}, status=500)


def _normalize_ids(data: dict) -> dict:
    """يحوّل ObjectIds لـ strings."""
    if not isinstance(data, dict):
        return data
    for key, value in data.items():
        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
            data[key] = str(value)
    return data


def _save_generated_file(db, data, file_content, filename, format_type, analysis_id):
    """يحفظ الملف المولّد في MongoDB."""
    try:
        from datetime import datetime
        explanation_id = data.get('_id', 'unknown')
        if hasattr(explanation_id, '__class__') and 'ObjectId' in str(explanation_id.__class__):
            explanation_id = str(explanation_id)

        try:
            analysis_id_obj = ObjectId(analysis_id) if ObjectId.is_valid(analysis_id) else analysis_id
        except:
            analysis_id_obj = analysis_id

        project_id = None
        try:
            analysis_results = db[settings.ANALYSIS_RESULTS_COLLECTION]
            analysis_data    = analysis_results.find_one({"_id": analysis_id_obj})
            if analysis_data:
                project_id = analysis_data.get('project_id')
                if not project_id and 'code_file_id' in analysis_data:
                    code_file = db[settings.CODE_FILES_COLLECTION].find_one({"_id": analysis_data['code_file_id']})
                    if code_file:
                        project_id = code_file.get('project_id') or code_file.get('source_project_id')
        except Exception as e:
            logger.warning(f"Could not fetch project_id: {e}")

        db[settings.GENERATED_FILES_COLLECTION].insert_one({
            'explanation_id': explanation_id,
            'analysis_id':    analysis_id_obj,
            'project_id':     project_id,
            'filename':       filename,
            'file_type':      FORMAT_DB_TYPE.get(format_type, format_type),
            'file_content':   file_content,
            'file_size':      len(file_content),
            'created_at':     datetime.utcnow(),
            'downloaded_count': 1
        })
        logger.info(f"[ExportHandler] File saved: {filename}")
    except Exception as e:
        logger.error(f"[ExportHandler] Save error: {e}")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def generate_document(request):
    """
    POST /api/analysis/generate-document/
    Body: { "code_file_id": "...", "document_format": "pdf|markdown|html|xml" }
    """
    try:
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
        else:
            data = request.GET.dict()

        code_file_id = data.get('code_file_id')
        if not code_file_id:
            return JsonResponse({"error": "code_file_id is required"}, status=400)
        return export_doc(request, code_file_id)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def export_doc(request, analysis_id):
    """
    GET/POST /api/analysis/export/<analysis_id>/

    Query params / Body:
        format : pdf | markdown | md | html | xml  (default: markdown)
        type   : high_level | low_level | ...       (default: high_level)
        mode   : display | download                 (default: display)
        image_url, user_email
    """
    logger.info(f"[ExportDoc] analysis_id:{analysis_id}")

    try:
        if request.method == 'POST':
            try:
                request_data = json.loads(request.body) if request.content_type == 'application/json' else request.POST.dict()
            except json.JSONDecodeError:
                request_data = {}
        else:
            request_data = request.GET.dict()

        mode             = request_data.get('mode', 'display').lower().strip()
        format_type      = (request_data.get('document_format') or request_data.get('format', 'markdown')).lower().strip()
        explanation_level = (request_data.get('explanation_level') or request_data.get('type', 'high_level')).lower().strip()
        image_url        = request_data.get('image_url', '').strip()
        user_email       = request_data.get('user_email', '').strip()

        # التحقق من الـ format
        if format_type not in SUPPORTED_FORMATS:
            return JsonResponse({
                "error": "Unsupported format",
                "message": f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
            }, status=400)

        # normalize
        if format_type in ['markdown', 'md']:
            format_type = 'md'

        # normalize explanation level
        high_vars = ['high', 'high_level', 'executive', 'business', 'high-level']
        low_vars  = ['low',  'low_level',  'technical', 'detailed', 'low-level']
        if any(v in explanation_level for v in high_vars):
            db_type = 'high_level'
        elif any(v in explanation_level for v in low_vars):
            db_type = 'low_level'
        else:
            db_type = 'high_level'

        logger.info(f"[ExportDoc] format:{format_type}, level:{explanation_level}→{db_type}, mode:{mode}")

        return handle_export_with_auto_generation(analysis_id, db_type, format_type, image_url, user_email, mode=mode)

    except Exception as e:
        logger.error(f"[ExportDoc] Error: {e}")
        return JsonResponse({"error": "System error", "message": str(e)}, status=500)


def list_generated_files_view(request):
    """
    GET /api/analysis/generated-files/
    GET /api/analysis/generated-files/?project_id=xxx
    """
    try:
        db = get_mongo_db()
        if db is None:
            return JsonResponse({"error": "Database connection error"}, status=500)

        query      = {}
        project_id = request.GET.get('project_id')
        if project_id:
            query['project_id'] = project_id

        files = list(db[settings.GENERATED_FILES_COLLECTION].find(query, {"file_content": 0}).sort("created_at", -1))

        for f in files:
            f['_id'] = str(f['_id'])
            for key in ('explanation_id', 'analysis_id'):
                if key in f:
                    f[key] = str(f[key])
            if 'project_id' in f and hasattr(f['project_id'], '__class__') and 'ObjectId' in str(f['project_id'].__class__):
                f['project_id'] = str(f['project_id'])

        response_data = {"files": files, "total": len(files)}
        if project_id:
            response_data["filter"] = {"project_id": project_id}

        return JsonResponse(response_data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def download_generated_file(request, file_id):
    """
    GET /api/analysis/download-generated-file/<file_id>/
    يدعم الآن تحميل html و xml إضافة لـ pdf و markdown.
    """
    logger.info(f"[DownloadFile] file_id:{file_id}")

    try:
        db = get_mongo_db()
        if db is None:
            return JsonResponse({"error": "Database connection error"}, status=500)

        try:
            file_data = db[settings.GENERATED_FILES_COLLECTION].find_one(
                {"_id": ObjectId(file_id) if ObjectId.is_valid(file_id) else file_id}
            )
        except:
            file_data = db[settings.GENERATED_FILES_COLLECTION].find_one({"_id": file_id})

        if not file_data:
            return JsonResponse({"error": "File not found", "message": f"File '{file_id}' not found"}, status=404)

        try:
            db[settings.GENERATED_FILES_COLLECTION].update_one(
                {"_id": file_data["_id"]}, {"$inc": {"downloaded_count": 1}}
            )
        except Exception as e:
            logger.warning(f"[DownloadFile] count update failed: {e}")

        filename     = file_data.get('filename', f'file_{file_id}')
        file_content = file_data.get('file_content', b'')
        file_type    = file_data.get('file_type', 'unknown')

        # تحويل Binary → bytes
        try:
            from bson.binary import Binary
            if isinstance(file_content, Binary):
                file_content = file_content.as_bytes()
            elif not isinstance(file_content, bytes):
                file_content = bytes(file_content) if file_content else b''
        except Exception as e:
            logger.warning(f"[DownloadFile] content conversion: {e}")
            file_content = b''

        # content-type وامتداد حسب file_type
        safe_filename = slugify(filename)
        if file_type == 'pdf':
            content_type  = 'application/pdf'
            if not safe_filename.lower().endswith('.pdf'):
                safe_filename += '.pdf'
        elif file_type == 'html':
            content_type  = 'text/html; charset=utf-8'
            if not safe_filename.lower().endswith('.html'):
                safe_filename += '.html'
        elif file_type == 'xml':
            content_type  = 'application/xml; charset=utf-8'
            if not safe_filename.lower().endswith('.xml'):
                safe_filename += '.xml'
        elif file_type == 'markdown':
            content_type  = 'text/markdown'
            if not safe_filename.lower().endswith(('.md', '.markdown')):
                safe_filename += '.md'
        else:
            content_type  = 'application/octet-stream'

        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')
        if not file_content:
            return JsonResponse({"error": "Empty file content"}, status=500)

        from urllib.parse import quote
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{quote(safe_filename)}"; filename*=UTF-8\'\'{quote(safe_filename)}'
        response['Content-Length']  = str(len(file_content))
        response['Cache-Control']   = 'no-cache, no-store, must-revalidate'
        response['Accept-Ranges']   = 'bytes'

        logger.info(f"[DownloadFile] Serving: {safe_filename}, {len(file_content)} bytes, {content_type}")
        return response

    except Exception as e:
        logger.error(f"[DownloadFile] Error: {e}")
        return JsonResponse({"error": "System error", "message": str(e)}, status=500)