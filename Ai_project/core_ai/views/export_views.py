import logging
import re
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from bson.objectid import ObjectId
from core_ai.mongo_utils import get_mongo_db
from core_ai.ai_engine.doc.markdown import MarkdownGenerator
from core_ai.ai_engine.doc.pdf import PDFGenerator
from core_ai.notification_utils import NotificationClient
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

logger = logging.getLogger(__name__)


def slugify(value):
    """
    تنظيف اسم الملف من الرموز غير الآمنة
    يحذف أي رموز خطيرة (/ \ : * ? " < > |) مع الحفاظ على الأحرف العربية والأرقام
    """
    if not value:
        return "file"
    
    value = str(value)
    # حذف الرموز الخطيرة فقط: / \ : * ? " < > |
    # الحفاظ على الأحرف العربية والأرقام والشرطات والنقاط
    value = re.sub(r'[/\\:*?"<>|]', '', value)
    # استبدال المسافات المتعددة بشرطة سفلية واحدة
    value = re.sub(r'\s+', '_', value.strip())
    # حذف الشرطات/النقاط المتعددة
    value = re.sub(r'[-_.]+', '_', value)
    # حذف الشرطات/النقاط من البداية والنهاية
    value = value.strip('-_')
    # التأكد من أن الاسم ليس فارغاً
    return value if value else "file"

try:
    from core_ai.celery_tasks.exp_task import generate_ai_explanation_task
    CELERY_AVAILABLE = True
except Exception as e:
    logger.warning(f"Celery not available: {e}")
    CELERY_AVAILABLE = False
    generate_ai_explanation_task = None


def handle_export_with_auto_generation(analysis_id, explanation_type, format_type, image_url=None, user_email=None, mode='display'):
    """
    نقطة الدخول الموحدة لتصدير التوثيق مع التوليد التلقائي
    تدعم جميع أنواع التصدير والتحقق التلقائي من وجود الشرح
    """
    logger.info(f"--- [ExportHandler] Starting export for analysis_id: {analysis_id}, type: {explanation_type} ---")
    
    try:
        db = get_mongo_db()
        if db is None:
            logger.error("--- [ExportHandler] Database connection failed ---")
            return JsonResponse({
                "error": "Database connection error",
                "message": "Failed to connect to MongoDB database"
            }, status=500)

        collection_name = getattr(settings, 'AI_EXPLANATIONS_COLLECTION', 'ai_explanations')
        
        try:
            if ObjectId.is_valid(analysis_id):
                analysis_obj_id = ObjectId(analysis_id)
            else:
                analysis_obj_id = analysis_id
        except:
            analysis_obj_id = analysis_id

        logger.info(f"--- [ExportHandler] Searching for explanation with analysis_id: {analysis_obj_id}, type: {explanation_type} ---")

        # Try searching by explanation_type first (new format)
        search_criteria_new = {
            "analysis_id": analysis_obj_id,
            "explanation_type": explanation_type
        }
        logger.info(f"--- [ExportHandler] Searching with criteria: {search_criteria_new} ---")
        data = db[collection_name].find_one(search_criteria_new)
        logger.info(f"--- [ExportHandler] Search result (explanation_type): {data is not None} ---")

        if data is not None:
            if not isinstance(data, dict):
                logger.warning(f"--- [ExportHandler] Invalid data type from new search: {type(data)} ---")
                data = None
            else:
                if '_id' in data and hasattr(data['_id'], '__class__') and 'ObjectId' in str(data['_id'].__class__):
                    data['_id'] = str(data['_id'])
                for key, value in data.items():
                    if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                        data[key] = str(value)

        if not data:
            # Fallback to exp_type (old format)
            search_criteria_old = {
                "analysis_id": analysis_obj_id,
                "exp_type": explanation_type
            }
            logger.info(f"--- [ExportHandler] Fallback search with criteria: {search_criteria_old} ---")
            data = db[collection_name].find_one(search_criteria_old)
            logger.info(f"--- [ExportHandler] Search result (exp_type): {data is not None} ---")

            if data is not None:
                if not isinstance(data, dict):
                    logger.warning(f"--- [ExportHandler] Invalid data type from old search: {type(data)} ---")
                    data = None
                else:
                    if '_id' in data and hasattr(data['_id'], '__class__') and 'ObjectId' in str(data['_id'].__class__):
                        data['_id'] = str(data['_id'])
                    for key, value in data.items():
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            data[key] = str(value)

        logger.info(f"--- [ExportHandler] Search result: {data is not None} ---")
        
        if data:
            logger.info(f"--- [ExportHandler] Data type: {type(data)} ---")
            if isinstance(data, dict):
                logger.info(f"--- [ExportHandler] Data _id type: {type(data.get('_id'))} ---")
            else:
                logger.warning(f"--- [ExportHandler] Data is not a dict, it's: {type(data)} ---")

        if not data:
            logger.info(f"--- [ExportHandler] Explanation not found in main collection, checking task status ---")
            
            tasks_collection = getattr(settings, 'AI_TASKS_COLLECTION', 'ai_tasks')
            task_data = db[tasks_collection].find_one({
                "analysis_id": analysis_id,
                "exp_type": explanation_type,
                "status": "completed"
            })
            
            if task_data and isinstance(task_data, dict) and task_data.get('result', {}).get('content'):
                logger.info(f"--- [ExportHandler] Found completed task with content ---")
                data = {
                    '_id': task_data.get('result', {}).get('explanation_id', 'temp_id'),
                    'content': task_data['result']['content'],
                    'exp_type': explanation_type,
                    'analysis_id': analysis_id,
                    'created_at': task_data.get('created_at')
                }
            else:
                logger.info(f"--- [ExportHandler] No completed task found either, generating new explanation ---")
                
                analysis_collection = getattr(settings, 'ANALYSIS_RESULTS_COLLECTION', 'analysis_results')
                analysis_data = db[analysis_collection].find_one({"_id": ObjectId(analysis_id) if ObjectId.is_valid(analysis_id) else analysis_id})
                
                if not analysis_data:
                    return JsonResponse({
                        "error": "Analysis not found",
                        "message": f"No analysis found with ID '{analysis_id}'. Code must be analyzed first.",
                        "suggestion": "Analyze the code first then try again"
                    }, status=404)
                
                if not CELERY_AVAILABLE or generate_ai_explanation_task is None:
                    return JsonResponse({
                        "error": "Generation system unavailable",
                        "message": "Celery system is currently unavailable. Cannot generate new explanation.",
                        "suggestion": "Make sure Celery and Redis are running"
                    }, status=503)
                
                try:
                    task = generate_ai_explanation_task.delay(analysis_id, explanation_type)
                    
                    return JsonResponse({
                        "status": "generating",
                        "message": "Generating requested explanation. Please wait...",
                        "task_id": task.id,
                        "analysis_id": analysis_id,
                        "explanation_type": explanation_type,
                        "estimated_time": "30-60 ثانية"
                    }, status=202)  # 202 Accepted
                except Exception as e:
                    logger.error(f"--- [ExportHandler] Celery task creation failed: {e} ---")
                    return JsonResponse({
                        "error": "Failed to start generation",
                        "message": f"An error occurred while starting explanation generation: {str(e)}",
                        "suggestion": "Make sure Celery and Redis are running"
                    }, status=503)

        if not data.get('content'):
            return JsonResponse({
                "error": "Empty content",
                "message": "Explanation exists but content is empty"
            }, status=404)

        if not isinstance(data, dict):
            logger.error(f"--- [ExportHandler] Invalid data type returned: {type(data)} ---")
            return JsonResponse({
                "error": "Invalid data",
                "message": f"Explanation found but data is invalid. Data type: {type(data)}"
            }, status=500)

        if not data.get('content'):
            logger.error(f"--- [ExportHandler] Missing content in data: {data.keys() if hasattr(data, 'keys') else 'No keys'} ---")
            return JsonResponse({
                "error": "Empty content",
                "message": "Explanation exists but content is empty"
            }, status=404)

        logger.info(f"--- [ExportHandler] Found explanation data: {type(data)} ---")
        logger.info(f"--- [ExportHandler] Data keys: {list(data.keys())} ---")

        if image_url:
            data['image_url'] = image_url

        try:
            logger.info(f"--- [ExportHandler] About to generate file with data type: {type(data)} ---")
            logger.info(f"--- [ExportHandler] Data content preview: {str(data)[:200]}... ---")

            content_value = data.get('content', '')
            logger.info(f"--- [ExportHandler] Content value type: {type(content_value)}, length: {len(str(content_value)) if content_value else 0} ---")

            if format_type == 'pdf':
                logger.info("--- [ExportHandler] Creating PDF generator ---")
                generator = PDFGenerator()
                content_type = 'application/pdf'
                
                # الحصول على اسم الملف من البيانات إن أمكن
                original_filename = data.get('filename', '')
                if not original_filename:
                    # محاولة استخراج اسم الملف من المحتوى
                    filename_match = re.search(r'File[:\s]+([^\s\n]+)', str(data.get('content', '')))
                    if filename_match:
                        original_filename = filename_match.group(1).strip()
                
                # تنظيف اسم الملف
                safe_name = slugify(original_filename) if original_filename else "technical_report"
                safe_explanation_type = slugify(explanation_type)
                safe_analysis_id = slugify(analysis_id[:8])
                
                # بناء اسم الملف النهائي مع التأكد من وجود .pdf
                # إزالة أي امتداد موجود مسبقاً
                base_name = f"{safe_name}_{safe_explanation_type}_{safe_analysis_id}"
                # إزالة أي امتداد موجود (.pdf, .txt, إلخ)
                base_name = re.sub(r'\.[^.]+$', '', base_name)
                # إضافة .pdf في النهاية
                filename = f"{base_name}.pdf"
                    
            else:
                logger.info("--- [ExportHandler] Creating Markdown generator ---")
                generator = MarkdownGenerator()
                content_type = 'text/markdown'
                
                # الحصول على اسم الملف من البيانات إن أمكن
                original_filename = data.get('filename', '')
                if not original_filename:
                    # محاولة استخراج اسم الملف من المحتوى
                    filename_match = re.search(r'File[:\s]+([^\s\n]+)', str(data.get('content', '')))
                    if filename_match:
                        original_filename = filename_match.group(1).strip()
                
                # تنظيف اسم الملف
                safe_name = slugify(original_filename) if original_filename else "technical_report"
                safe_explanation_type = slugify(explanation_type)
                safe_analysis_id = slugify(analysis_id[:8])
                
                # بناء اسم الملف النهائي مع التأكد من وجود .md
                # إزالة أي امتداد موجود مسبقاً
                base_name = f"{safe_name}_{safe_explanation_type}_{safe_analysis_id}"
                # إزالة أي امتداد موجود (.md, .txt, إلخ)
                base_name = re.sub(r'\.[^.]+$', '', base_name)
                # إضافة .md في النهاية
                filename = f"{base_name}.md"

            logger.info(f"--- [ExportHandler] Calling generator.generate() with content type: {type(content_value)} ---")
            logger.info(f"--- [ExportHandler] Data keys before generator: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'} ---")
            logger.info(f"--- [ExportHandler] Data content length: {len(content_value) if isinstance(content_value, str) else 'N/A'} ---")
            
            try:
                file_content = generator.generate(data)
            except Exception as pdf_error:
                logger.error(f"--- [ExportHandler] PDF generation failed: {str(pdf_error)} ---")
                
                # If PDF generation fails, fallback to Markdown
                if format_type == 'pdf':
                    logger.info("--- [ExportHandler] Falling back to Markdown due to PDF generation failure ---")
                    format_type = 'md'
                    generator = MarkdownGenerator()
                    file_content = generator.generate(data)
                    filename = filename.replace('.pdf', '.md')
                else:
                    raise

            if not file_content:
                return JsonResponse({
                    "error": "File generation failed",
                    "message": f"Failed to generate {format_type} file"
                }, status=500)

            logger.info(f"--- [ExportHandler] File generated successfully, size: {len(file_content)} bytes ---")

            try:
                from datetime import datetime
                
                if isinstance(data, dict):
                    explanation_id = data.get('_id', 'unknown')
                    if hasattr(explanation_id, '__class__') and 'ObjectId' in str(explanation_id.__class__):
                        explanation_id = str(explanation_id)
                else:
                    explanation_id = 'unknown'
                
                try:
                    if ObjectId.is_valid(analysis_id):
                        analysis_id_obj = ObjectId(analysis_id)
                    else:
                        analysis_id_obj = analysis_id
                except:
                    analysis_id_obj = analysis_id
                
                project_id = None
                try:
                    # محاولة جلب project_id من AnalysisResult
                    analysis_results_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]
                    analysis_data = analysis_results_collection.find_one({"_id": analysis_id_obj})
                    
                    if analysis_data:
                        # إذا كان موجود في AnalysisResult
                        project_id = analysis_data.get('project_id')
                        
                        # إذا لم يكن موجود، جرب من CodeFile
                        if not project_id and 'code_file_id' in analysis_data:
                            code_files_collection = db[settings.CODE_FILES_COLLECTION]
                            code_file_data = code_files_collection.find_one(
                                {"_id": analysis_data['code_file_id']}
                            )
                            if code_file_data:
                                project_id = code_file_data.get('project_id') or code_file_data.get('source_project_id')
                    
                    logger.info(f"--- [ExportHandler] Found project_id: {project_id} ---")
                except Exception as e:
                    logger.warning(f"--- [ExportHandler] Could not fetch project_id: {e} ---")
                    project_id = None
                
                file_record = {
                    'explanation_id': explanation_id,
                    'analysis_id': analysis_id_obj,
                    'project_id': project_id,  
                    'filename': filename,
                    'file_type': 'pdf' if format_type == 'pdf' else 'markdown',
                    'file_content': file_content,
                    'file_size': len(file_content),
                    'created_at': datetime.utcnow(),
                    'downloaded_count': 1
                }
                result = db[settings.GENERATED_FILES_COLLECTION].insert_one(file_record)
                logger.info(f"--- [ExportHandler] File saved to database with ID: {result.inserted_id} ---")
            except Exception as e:
                logger.error(f"--- [ExportHandler] Error saving file to database: {e} ---")

            if user_email:
                try:
                    NotificationClient.send_documentation_notification(
                        user_email=user_email,
                        file_name=filename,
                        file_type=format_type,
                        project_name="analysis code",
                        user_name=""
                    )
                except Exception as notification_error:
                    logger.warning(f"Failed to send export notification: {str(notification_error)}")

            # التعديل عند العودة بالـ Response بناءً على mode
            if mode == 'display':
                # إذا كان المطلوب عرض فقط، نرسل المحتوى كـ JSON ليعرضه الفرونت آند
                return JsonResponse({
                    "status": "success",
                    "format": format_type,
                    "content": data.get('content', ''),  # المحتوى النصي (Markdown)
                    "filename": filename
                })
            else:
                # إذا كان المطلوب download، نرسل الـ HttpResponse الأصلي كملف
                from urllib.parse import quote
                
                # التأكد من أن المحتوى هو bytes وليس string
                if isinstance(file_content, str):
                    file_content = file_content.encode('utf-8')
                elif not isinstance(file_content, bytes):
                    file_content = bytes(file_content)
                
                # التأكد من أن المحتوى ليس فارغاً
                if not file_content or len(file_content) == 0:
                    logger.error("--- [ExportHandler] Generated file content is empty ---")
                    return JsonResponse({
                        "error": "Empty file content",
                        "message": "The generated file is empty. Please check the PDF generation logs."
                    }, status=500)
                
                # إنشاء الـ Response مع التأكد من content-type الصحيح
                response = HttpResponse(file_content, content_type=content_type)
                
                # إضافة headers إضافية لضمان التحميل الصحيح
                response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
                response['Content-Length'] = str(len(file_content))
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                # التأكد من أن الـ response لا يتم تشفيره
                response['Accept-Ranges'] = 'bytes'
                
                logger.info(f"--- [ExportHandler] Returning PDF response: {len(file_content)} bytes, content-type: {content_type} ---")
                return response

        except Exception as e:
            logger.error(f"--- [ExportHandler] Generation error: {str(e)} ---")

            error_msg = str(e)
            if "cairo" in error_msg.lower() or "pdf" in error_msg.lower() and "not supported" in error_msg.lower() or "weasyprint" in error_msg.lower():
                return JsonResponse({
                    "error": "PDF not supported",
                    "message": "PDF file generation is currently unavailable due to missing Cairo/WeasyPrint libraries. Please use Markdown format instead.",
                    "suggestion": "Use format=md in the request instead of format=pdf"
                }, status=503)

            return JsonResponse({
                "error": "File generation error",
                "message": f"An error occurred during file generation: {str(e)}"
            }, status=500)

    except Exception as e:
        logger.error(f"--- [ExportHandler] Error: {str(e)} ---")
        return JsonResponse({
            "error": "System error",
            "message": f"An error occurred while processing the request: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def generate_document(request):
    """
    Generate document without requiring analysis_id
    
    POST Body:
    - code_file_id: required (string)
    - document_format: pdf|markdown (default: markdown)
    - explanation_level: high_level|low_level (default: high_level)
    - include_diagram: boolean (default: true)
    - include_explanation: boolean (default: true)
    """
    try:
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
        else:
            data = request.GET.dict()
        
        code_file_id = data.get('code_file_id')
        if not code_file_id:
            return JsonResponse({
                "error": "code_file_id is required",
                "message": "Please provide code_file_id in the request body"
            }, status=400)
        
        # Use code_file_id as analysis_id (they're the same in our system)
        return export_doc(request, code_file_id)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body"
        }, status=400)
    except Exception as e:
        logger.error(f"Error in generate_document: {e}")
        return JsonResponse({
            "error": "Internal server error",
            "message": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def export_doc(request, analysis_id):
    """
    نقطة الدخول الموحدة لتصدير التوثيق
    
    URL: /api/export/<str:analysis_id>/
    
    Query Parameters أو POST Body:
    - format: pdf|markdown (افتراضي: pdf)
    - type: high|low|detailed (افتراضي: detailed) 
    - mode: display|download (افتراضي: display)
    - image_url: رابط الصورة (اختياري)
    
    - إذا كان mode=display: يرجع JSON response مع المحتوى النصي للعرض
    - إذا كان mode=download: يرجع الملف مباشرة للتحميل
    """
    logger.info(f"--- [ExportDoc] Export request for analysis_id: {analysis_id} ---")
    
    try:
        if request.method == 'POST':
            try:
                if request.content_type == 'application/json':
                    request_data = json.loads(request.body)
                else:
                    request_data = request.POST.dict()
            except json.JSONDecodeError:
                request_data = {}
        else:
            request_data = request.GET.dict()

        # Support both frontend and backend parameter names
        mode = request_data.get('mode', 'display').lower().strip()
        
        # document_format from frontend or format from backend
        format_type = request_data.get('document_format') or request_data.get('format', 'markdown')
        format_type = format_type.lower().strip()
        
        # explanation_level from frontend or type from backend
        explanation_level = request_data.get('explanation_level') or request_data.get('type', 'high_level')
        explanation_level = explanation_level.lower().strip()
        
        image_url = request_data.get('image_url', '').strip()
        user_email = request_data.get('user_email', '').strip()

        if format_type not in ['pdf', 'markdown', 'md']:
            return JsonResponse({
                "error": "Unsupported format",
                "message": "Supported formats: pdf, markdown, md"
            }, status=400)

        if explanation_level not in ['high_level', 'low_level', 'high', 'low', 'detailed']:
            return JsonResponse({
                "error": "Unsupported explanation level",
                "message": "Supported levels: high_level, low_level, high, low, detailed"
            }, status=400)

        if format_type in ['markdown', 'md']:
            format_type = 'md'

                # ✅ الكود المصحح
        # Normalize explanation levels - support all variations
        explanation_level_lower = str(explanation_level).strip().lower()

        # Define all possible variations
        high_level_variations = ['high', 'high_level', 'executive', 'business', 'high-level', 'high level']
        low_level_variations = ['low', 'low_level', 'technical', 'detailed', 'low-level', 'low level']

        # Determine the actual type
        if any(variant in explanation_level_lower for variant in high_level_variations):
            db_explanation_type = 'high_level'
        elif any(variant in explanation_level_lower for variant in low_level_variations):
            db_explanation_type = 'low_level'
        else:
            # Default to high_level if unknown
            db_explanation_type = 'high_level'

        logger.info(f"--- [ExportDoc] Parameters - Mode: {mode}, Format: {format_type}, Level: {explanation_level} -> DB Type: {db_explanation_type} ---")

        return handle_export_with_auto_generation(analysis_id, db_explanation_type, format_type, image_url, user_email, mode=mode)

    except Exception as e:
        logger.error(f"--- [ExportDoc] Error: {str(e)} ---")
        return JsonResponse({
            "error": "System error",
            "message": f"An error occurred while processing the request: {str(e)}"
        }, status=500)


def list_generated_files_view(request):
    """
    جلب قائمة بكل ملفات التوثيق التي تم توليدها وتخزينها
    
    URL: /api/generated-files/
    URL: /api/generated-files/?project_id=xxx  # ✅ جديد - فلترة حسب المشروع
    """
    try:
        db = get_mongo_db()
        if db is None:
            return JsonResponse({
                "error": "Database connection error"
            }, status=500)

        # ✅ إضافة: بناء query بناءً على project_id
        query = {}
        project_id = request.GET.get('project_id')  # ✅ جديد
        
        if project_id:
            # ✅ فلترة حسب project_id
            query['project_id'] = project_id
            logger.info(f"--- [ListFiles] Filtering by project_id: {project_id} ---")
        
        # ✅ تعديل: استخدام query بدلاً من {}
        files = list(db[settings.GENERATED_FILES_COLLECTION].find(
            query,  # ✅ تم التعديل هنا
            {"file_content": 0}
        ).sort("created_at", -1))

        for f in files:
            f['_id'] = str(f['_id'])
            if 'explanation_id' in f: 
                f['explanation_id'] = str(f['explanation_id'])
            if 'analysis_id' in f:
                f['analysis_id'] = str(f['analysis_id'])
            # ✅ إضافة: تحويل project_id إلى string إذا كان ObjectId
            if 'project_id' in f and hasattr(f['project_id'], '__class__') and 'ObjectId' in str(f['project_id'].__class__):
                f['project_id'] = str(f['project_id'])

        # ✅ إضافة: معلومات إضافية في الاستجابة
        response_data = {
            "files": files,
            "total": len(files)
        }
        
        if project_id:
            response_data["filter"] = {"project_id": project_id}

        return JsonResponse(response_data, safe=False)

    except Exception as e:
        logger.error(f"--- [ListFiles] Error: {e} ---")
        return JsonResponse({"error": str(e)}, status=500)


def download_generated_file(request, file_id):
    """
    تحميل ملف مولد من قاعدة البيانات
    URL: /api/download-generated-file/<str:file_id>/
    """
    logger.info(f"--- [DownloadGeneratedFile] Request for file ID: {file_id} ---")

    try:
        db = get_mongo_db()
        if db is None:
            logger.error("--- [DownloadGeneratedFile] Database connection failed ---")
            return JsonResponse({
                "error": "Database connection error",
                "message": "Failed to connect to MongoDB database"
            }, status=500)

        try:
            if ObjectId.is_valid(file_id):
                file_data = db[settings.GENERATED_FILES_COLLECTION].find_one({"_id": ObjectId(file_id)})
            else:
                file_data = db[settings.GENERATED_FILES_COLLECTION].find_one({"_id": file_id})
        except:
            file_data = db[settings.GENERATED_FILES_COLLECTION].find_one({"_id": file_id})

        if not file_data:
            logger.warning(f"--- [DownloadGeneratedFile] File not found: {file_id} ---")
            return JsonResponse({
                "error": "File not found",
                "message": f"File with ID '{file_id}' not found"
            }, status=404)

        try:
            db[settings.GENERATED_FILES_COLLECTION].update_one(
                {"_id": file_data["_id"]},
                {"$inc": {"downloaded_count": 1}}
            )
        except Exception as e:
            logger.warning(f"--- [DownloadGeneratedFile] Failed to update download count: {e} ---")

        filename = file_data.get('filename', f'generated_file_{file_id}')
        file_content = file_data.get('file_content', b'')
        
        # التحويل من Binary إلى bytes إذا كان MongoDB أعاد Binary
        try:
            from bson.binary import Binary
            if isinstance(file_content, Binary):
                file_content = file_content.as_bytes()
            elif isinstance(file_content, bytes):
                pass  # Already bytes
            else:
                # محاولة التحويل إلى bytes
                file_content = bytes(file_content) if file_content else b''
        except (ImportError, TypeError, ValueError) as e:
            logger.warning(f"--- [DownloadGeneratedFile] Error converting file_content: {e} ---")
            if not isinstance(file_content, bytes):
                file_content = b''
        
        file_type = file_data.get('file_type', 'unknown')

        # تنظيف اسم الملف من الرموز غير الآمنة
        safe_filename = slugify(filename)
        
        # التأكد من وجود الامتداد الصحيح
        if file_type == 'pdf':
            content_type = 'application/pdf'
            if not safe_filename.lower().endswith('.pdf'):
                safe_filename = f"{safe_filename.rstrip('.')}.pdf"
        elif file_type == 'markdown':
            content_type = 'text/markdown'
            if not safe_filename.lower().endswith(('.md', '.markdown')):
                safe_filename = f"{safe_filename.rstrip('.')}.md"
        else:
            content_type = 'application/octet-stream'

        logger.info(f"--- [DownloadGeneratedFile] Serving file: {safe_filename}, size: {len(file_content)} bytes ---")

        # التأكد من أن المحتوى هو bytes وليس string
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')
        elif not isinstance(file_content, bytes):
            try:
                file_content = bytes(file_content)
            except (TypeError, ValueError):
                logger.error(f"--- [DownloadGeneratedFile] Cannot convert file_content to bytes: {type(file_content)} ---")
                return JsonResponse({
                    "error": "Invalid file content",
                    "message": "File content is not in a valid format"
                }, status=500)
        
        # التأكد من أن المحتوى ليس فارغاً
        if not file_content or len(file_content) == 0:
            logger.error(f"--- [DownloadGeneratedFile] File content is empty for file_id: {file_id} ---")
            return JsonResponse({
                "error": "Empty file content",
                "message": "The requested file is empty or corrupted"
            }, status=500)

        # استخدام quote في Content-Disposition لضمان الترميز الصحيح
        from urllib.parse import quote
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{quote(safe_filename)}"; filename*=UTF-8\'\'{quote(safe_filename)}'
        response['Content-Length'] = str(len(file_content))
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['Accept-Ranges'] = 'bytes'

        logger.info(f"--- [DownloadGeneratedFile] Returning file response: {len(file_content)} bytes, content-type: {content_type} ---")
        return response

    except Exception as e:
        logger.error(f"--- [DownloadGeneratedFile] Error: {str(e)} ---")
        return JsonResponse({
            "error": "خطأ في النظام",
            "message": f"حدث خطأ أثناء تحميل الملف: {str(e)}"
        }, status=500)