"""
views/folder_upload.py  ← معدّل
======================
التغييرات عن النسخة القديمة:
    1. ملف واحد عادي → يُحفظ داخل مجلد اسمه project_name تلقائياً (مش يُعامل كملف بدون مجلد)
    2. ملفات متعددة بدون مسار → تُحفظ داخل مجلد project_name
    3. الـ versioning يعتمد على upm_project_id (UUID من MySQL) مش project_name فقط
    4. response يرجع filepath لكل ملف لدعم رسم الشجرة في الفرونت
"""

import io, os, uuid, hashlib, zipfile, logging
from datetime import datetime

from bson import ObjectId
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from core_ai.mongo_utils import get_mongo_db, save_to_gridfs
from core_ai.models.codefile import CodeFile
from core_ai.celery_tasks.analyze_task import analyze_code_file_task

logger = logging.getLogger(__name__)

EXTENSION_MAP = {
    '.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
    '.cs': 'csharp', '.cpp': 'cpp', '.c': 'c', '.rb': 'ruby', '.go': 'go', '.kt': 'kotlin',
}
IGNORED_PREFIXES = ('__MACOSX', '.', '__pycache__')
IGNORED_EXTENSIONS = ('.pyc', '.class', '.exe', '.dll', '.so', '.o')
PROJECT_VERSIONS_COLLECTION = 'project_versions'


@method_decorator(csrf_exempt, name='dispatch')
class FolderUploadView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        logger.info("[FOLDER-UPLOAD] Request received")

        project_name = request.data.get('project_name', '').strip()
        if not project_name:
            return Response({"error": "project_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        # upm_project_id هو UUID المشروع الحقيقي من MySQL — هو الأساس للـ versioning
        upm_project_id = request.data.get('upm_project_id', '').strip()
        if not upm_project_id:
            upm_project_id = project_name  # fallback للتوافق
            logger.warning("[FOLDER-UPLOAD] upm_project_id not provided, falling back to project_name")

        try:
            files_data = self._extract_files(request, project_name)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] Extraction error: {e}")
            return Response({"error": "Failed to process uploaded files"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not files_data:
            return Response(
                {"error": "No supported files found. Supported: .py .java .js .ts .cs .cpp .rb .go .kt"},
                status=status.HTTP_400_BAD_REQUEST
            )

        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # حساب رقم الإصدار بناءً على upm_project_id الحقيقي
        version_number = self._get_next_version(db, upm_project_id)
        logger.info(f"[FOLDER-UPLOAD] project_id={upm_project_id}, version={version_number}")

        try:
            file_ids_list, skipped = self._save_files(db, files_data, upm_project_id, project_name, version_number, request)
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] Save error: {e}")
            return Response({"error": f"Failed to save files: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        file_ids = [f["file_id"] for f in file_ids_list]
        self._save_project_version(db, upm_project_id, project_name, version_number, file_ids, request)

        logger.info(f"[FOLDER-UPLOAD] Done — version={version_number}, saved={len(file_ids_list)}, skipped={skipped}")

        return Response({
            "project_id":     upm_project_id,
            "project_name":   project_name,
            "version_number": version_number,
            "file_count":     len(file_ids_list),
            "file_ids":       file_ids,
            "files":          file_ids_list,
            "skipped":        skipped,
        }, status=status.HTTP_201_CREATED)

    def _get_next_version(self, db, upm_project_id):
        """يحسب رقم الإصدار القادم بناءً على upm_project_id — مش project_name."""
        collection = db[PROJECT_VERSIONS_COLLECTION]
        last_version = collection.find_one(
            {"project_id": upm_project_id},
            sort=[("version_number", -1)]
        )
        if last_version:
            v = last_version["version_number"] + 1
            logger.info(f"[FOLDER-UPLOAD] Existing project, new version: {v}")
            return v
        logger.info("[FOLDER-UPLOAD] New project: version 1")
        return 1

    def _save_project_version(self, db, project_id, project_name, version_number, file_ids, request):
        collection = db[PROJECT_VERSIONS_COLLECTION]
        user_email = request.user.email if request.user.is_authenticated else request.data.get('user_email')
        collection.insert_one({
            "project_id":     project_id,
            "project_name":   project_name,
            "version_number": version_number,
            "file_ids":       file_ids,
            "total_files":    len(file_ids),
            "user_email":     user_email,
            "created_at":     datetime.utcnow(),
        })
        logger.info(f"[FOLDER-UPLOAD] ProjectVersion saved: v{version_number}")

    def _extract_files(self, request, project_name):
        """
        القاعدة الجديدة:
            - ملف واحد أو ملفات بدون مسار → filepath = project_name/filename
            - ملفات مع مسار (folder upload من المتصفح) → يُحافظ على المسار
            - ZIP → يُفكّ مع الحفاظ على بنية المجلدات
        """
        all_files = (
            list(request.FILES.getlist('file')) +
            list(request.FILES.getlist('files')) +
            list(request.FILES.getlist('folder'))
        )

        if not all_files:
            raise ValueError("No files received. Send 'files' (multiple) or 'file' (single/ZIP).")

        # ZIP
        if len(all_files) == 1 and all_files[0].name.lower().endswith('.zip'):
            logger.info(f"[FOLDER-UPLOAD] Processing ZIP: {all_files[0].name}")
            return self._extract_from_zip(all_files[0])

        archives = [f for f in all_files if f.name.lower().endswith('.zip')]
        if archives:
            result = []
            for f in archives:
                result.extend(self._extract_from_zip(f))
            if result:
                return result

        logger.info(f"[FOLDER-UPLOAD] Processing {len(all_files)} file(s)")
        return self._extract_from_files(all_files, project_name)

    def _extract_from_zip(self, uploaded_file):
        result = []
        try:
            raw = uploaded_file.read()
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for entry in zf.namelist():
                    if entry.endswith('/'):
                        continue
                    basename = os.path.basename(entry)
                    if not basename or any(basename.startswith(p) for p in IGNORED_PREFIXES):
                        continue
                    ext = os.path.splitext(entry)[1].lower()
                    if ext in IGNORED_EXTENSIONS or ext not in EXTENSION_MAP:
                        continue
                    try:
                        content = zf.read(entry).decode('utf-8', errors='ignore')
                        result.append((entry, content))
                    except Exception as e:
                        logger.warning(f"[FOLDER-UPLOAD] Skipping {entry}: {e}")
        except zipfile.BadZipFile:
            raise ValueError("Invalid ZIP file.")
        logger.info(f"[FOLDER-UPLOAD] Extracted {len(result)} files from ZIP")
        return result

    def _extract_from_files(self, files, project_name):
        """
        لو f.name فيه مسار (src/utils.py) → نستخدمه كما هو
        لو f.name هو اسم الملف فقط (utils.py) → project_name/utils.py
        """
        result = []
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if ext in IGNORED_EXTENSIONS or ext not in EXTENSION_MAP:
                continue
            basename = os.path.basename(f.name)
            if not basename or any(basename.startswith(p) for p in IGNORED_PREFIXES):
                continue
            try:
                content = f.read().decode('utf-8', errors='ignore')
                if os.path.dirname(f.name):
                    filepath = f.name
                else:
                    # ملف واحد أو ملفات بدون مسار → تحت مجلد المشروع
                    filepath = f"{project_name}/{f.name}"
                result.append((filepath, content))
            except Exception as e:
                logger.warning(f"[FOLDER-UPLOAD] Skipping {f.name}: {e}")
        logger.info(f"[FOLDER-UPLOAD] Read {len(result)} file(s)")
        return result

    def _save_files(self, db, files_data, project_id, project_name, version_number, request):
        collection = db[settings.CODE_FILES_COLLECTION]
        analysis_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]
        files_list = []
        skipped = 0
        user_email = request.user.email if request.user.is_authenticated else request.data.get('user_email')
        user_name = request.user.username if request.user.is_authenticated else None

        for filepath, file_content in files_data:
            try:
                file_info = self._save_single_file(
                    collection, analysis_collection,
                    filepath, file_content, project_id, project_name,
                    version_number, user_email, user_name
                )
                files_list.append(file_info)
            except Exception as e:
                logger.error(f"[FOLDER-UPLOAD] Failed to save {filepath}: {e}")
                skipped += 1

        return files_list, skipped

    def _save_single_file(self, collection, analysis_collection, filepath, content,
                          project_id, project_name, version_number, user_email, user_name):
        file_hash = hashlib.md5(content.encode()).hexdigest()

        existing = collection.find_one({'file_hash': file_hash, 'source_project_id': project_id})
        if existing:
            logger.info(f"[FOLDER-UPLOAD] Reusing: {filepath} (id={existing['_id']})")
            return {
                "file_id":        str(existing['_id']),
                "filename":       os.path.basename(filepath),
                "filepath":       filepath,
                "file_type":      existing.get('file_type', 'unknown'),
                "version_number": existing.get('version_number', version_number),
            }

        ext = os.path.splitext(filepath)[1].lower()
        file_type = EXTENSION_MAP.get(ext, 'unknown')
        basename = os.path.basename(filepath)

        gridfs_id = save_to_gridfs(
            content=content,
            filename=basename,
            metadata={'project_id': project_id, 'filepath': filepath, 'file_type': file_type,
                      'file_hash': file_hash, 'version': version_number}
        )

        code_file = CodeFile(
            filename=basename, file_type=file_type, file_hash=file_hash,
            gridfs_id=gridfs_id, file_size=len(content.encode('utf-8')),
            source_project_id=project_id, project_name=project_name,
            version_number=version_number, user_email=user_email,
            user_name=user_name, analysis_status="PENDING",
        )

        data_to_insert = code_file.dict(by_alias=True, exclude_unset=True)
        data_to_insert['filepath'] = filepath
        if '_id' in data_to_insert and data_to_insert['_id'] is None:
            del data_to_insert['_id']

        result = collection.insert_one(data_to_insert)
        file_id = str(result.inserted_id)
        logger.info(f"[FOLDER-UPLOAD] Saved: {filepath} → GridFS:{gridfs_id}, Mongo:{file_id}")

        analyze_code_file_task.delay(file_id)

        return {
            "file_id":        file_id,
            "filename":       basename,
            "filepath":       filepath,
            "file_type":      file_type,
            "version_number": version_number,
        }