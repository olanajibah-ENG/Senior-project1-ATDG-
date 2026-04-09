"""
views/folder_upload.py
======================
FolderUploadView — معالجة رفع المجلدات والملفات المتعددة

يدعم 3 طرق رفع:
    1. ملفات متعددة مباشرة  → request.FILES.getlist('files')
    2. ملف ZIP مضغوط       → request.FILES.get('file') ينتهي بـ .zip
    3. مجلد كامل من المتصفح → نفس الطريقة 1 لكن file.name يحتوي المسار

الـ endpoint: POST /folder-upload/
الـ Response:  { project_id, project_name, version_number, file_count, file_ids[], skipped }
"""

import io
import os
import uuid
import hashlib
import zipfile
import logging
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

# ── الامتدادات المدعومة ────────────────────────────────────────────────────────
EXTENSION_MAP = {
    '.py':   'python',
    '.java': 'java',
    '.js':   'javascript',
    '.ts':   'typescript',
    '.cs':   'csharp',
    '.cpp':  'cpp',
    '.c':    'c',
    '.rb':   'ruby',
    '.go':   'go',
    '.kt':   'kotlin',
}

IGNORED_PREFIXES = ('__MACOSX', '.', '__pycache__')
IGNORED_EXTENSIONS = ('.pyc', '.class', '.exe', '.dll', '.so', '.o')

PROJECT_VERSIONS_COLLECTION = 'project_versions'


@method_decorator(csrf_exempt, name='dispatch')
class FolderUploadView(APIView):
    """
    POST /folder-upload/

    Body (multipart/form-data):
        project_name  : str    — اسم المشروع (مطلوب)
        files         : File[] — ملفات متعددة أو مجلد كامل
        file          : File   — ملف ZIP واحد (بديل عن files)

    Response 201:
        {
            "project_id"    : "uuid",
            "project_name"  : "my_project",
            "version_number": 1,
            "file_count"    : 5,
            "file_ids"      : ["id1", "id2", ...],
            "skipped"       : 0
        }
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    # ── Entry point ────────────────────────────────────────────────────────────
    def post(self, request):
        logger.info("[FOLDER-UPLOAD] Request received")

        # 1. التحقق من project_name
        project_name = request.data.get('project_name', '').strip()
        if not project_name:
            return Response(
                {"error": "project_name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. استخراج الملفات من الطلب
        try:
            files_data = self._extract_files(request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] Extraction error: {e}")
            return Response(
                {"error": "Failed to process uploaded files"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not files_data:
            return Response(
                {"error": "No supported files found. Supported: .py .java .js .ts .cs .cpp .rb .go .kt"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. اتصال بـ MongoDB
        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Database connection failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 4. تحديد project_id و version_number
        # لو المشروع موجود → إصدار جديد، لو لا → إصدار 1 جديد
        project_id, version_number = self._get_or_create_project(
            db, project_name, request
        )
        logger.info(f"[FOLDER-UPLOAD] project_id={project_id}, version={version_number}")

        # 5. حفظ الملفات في MongoDB + GridFS
        try:
            file_ids_list, skipped = self._save_files(
                db, files_data, project_id, project_name, version_number, request
            )
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] Save error: {e}")
            return Response(
                {"error": f"Failed to save files: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 6. حفظ ProjectVersion document
        file_ids = [f["file_id"] for f in file_ids_list]
        self._save_project_version(
            db, project_id, project_name, version_number, file_ids
        )

        logger.info(
            f"[FOLDER-UPLOAD] Done — version={version_number}, "
            f"saved={len(file_ids_list)}, skipped={skipped}"
        )

        return Response(
            {
                "project_id":     project_id,
                "project_name":   project_name,
                "version":        version_number,
                "file_count":     len(file_ids_list),
                "file_ids":       [f["file_id"] for f in file_ids_list],
                "files":          file_ids_list,
                "skipped":        skipped,
            },
            status=status.HTTP_201_CREATED
        )

    # ── تحديد المشروع والإصدار ─────────────────────────────────────────────────
    def _get_or_create_project(self, db, project_name, request):
        """
        يتحقق إذا المشروع موجود بنفس الاسم ونفس المستخدم.
        لو موجود → يرجع نفس الـ project_id مع version+1
        لو مش موجود → يرجع project_id جديد مع version=1
        """
        collection = db[PROJECT_VERSIONS_COLLECTION]
        user_email = request.user.email if request.user.is_authenticated else None

        # ابحث عن آخر إصدار لهاد المشروع
        query = {"project_name": project_name}
        if user_email:
            query["user_email"] = user_email

        last_version = collection.find_one(
            query,
            sort=[("version_number", -1)]  # آخر إصدار
        )

        if last_version:
            # المشروع موجود → إصدار جديد
            project_id = last_version["project_id"]
            version_number = last_version["version_number"] + 1
            logger.info(f"[FOLDER-UPLOAD] Existing project found, new version: {version_number}")
        else:
            # مشروع جديد
            project_id = str(uuid.uuid4())
            version_number = 1
            logger.info(f"[FOLDER-UPLOAD] New project created: {project_id}")

        return project_id, version_number

    # ── حفظ ProjectVersion ─────────────────────────────────────────────────────
    def _save_project_version(self, db, project_id, project_name, version_number, file_ids):
        """يحفظ record في project_versions collection."""
        collection = db[PROJECT_VERSIONS_COLLECTION]
        collection.insert_one({
            "project_id":     project_id,
            "project_name":   project_name,
            "version_number": version_number,
            "file_ids":       file_ids,
            "total_files":    len(file_ids),
            "created_at":     datetime.utcnow(),
        })
        logger.info(f"[FOLDER-UPLOAD] ProjectVersion saved: v{version_number}")

    # ── استخراج الملفات من الطلب ───────────────────────────────────────────────
    def _extract_files(self, request):
        """
        ترجع list من tuples: [(filepath, content), ...]
        filepath = المسار الكامل مثل src/utils.py
        """
        # ── جمع كل الملفات من أي field ────────────────────────────────────────
        all_single = list(request.FILES.getlist('file'))
        all_multi  = list(request.FILES.getlist('files')) + list(request.FILES.getlist('folder'))
        all_files  = all_single + all_multi

        if not all_files:
            raise ValueError(
                "No files received. Send 'files' (multiple files) or 'file' (ZIP/RAR archive)."
            )

        # ── لو ملف واحد مضغوط (ZIP) ──────────────────────────────────────────
        if len(all_files) == 1:
            f = all_files[0]
            if f.name.lower().endswith('.zip'):
                logger.info(f"[FOLDER-UPLOAD] Processing ZIP: {f.name}")
                return self._extract_from_zip(f)

        # ── لو أكثر من ملف: تحقق لو كلهم ZIP ─────────────────────────────────
        archives = [f for f in all_files if f.name.lower().endswith('.zip')]
        if archives:
            result = []
            for f in archives:
                logger.info(f"[FOLDER-UPLOAD] Processing ZIP: {f.name}")
                result.extend(self._extract_from_zip(f))
            if result:
                return result

        # ── ملفات عادية متعددة ─────────────────────────────────────────────────
        logger.info(f"[FOLDER-UPLOAD] Processing {len(all_files)} files")
        return self._extract_from_files(all_files)

    def _extract_from_zip(self, uploaded_file):
        """فك ZIP وإرجاع (filepath, content) للملفات المدعومة."""
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
                        result.append((entry, content))  # entry = المسار الكامل
                    except Exception as e:
                        logger.warning(f"[FOLDER-UPLOAD] Skipping {entry}: {e}")
        except zipfile.BadZipFile:
            raise ValueError("Invalid ZIP file. Please upload a valid ZIP archive.")

        logger.info(f"[FOLDER-UPLOAD] Extracted {len(result)} files from ZIP")
        return result

    def _extract_from_files(self, files):
        """قراءة ملفات متعددة مباشرة — يحافظ على المسار الكامل."""
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
                result.append((f.name, content))  # f.name = المسار الكامل
            except Exception as e:
                logger.warning(f"[FOLDER-UPLOAD] Skipping {f.name}: {e}")
        logger.info(f"[FOLDER-UPLOAD] Read {len(result)} files from multipart")
        return result

    # ── حفظ الملفات في MongoDB + GridFS ───────────────────────────────────────
    def _save_files(self, db, files_data, project_id, project_name, version_number, request):
        """
        يحفظ كل ملف كـ CodeFile في MongoDB والمحتوى في GridFS.
        يرجع: (files: list of dicts, skipped: int)
        """
        collection = db[settings.CODE_FILES_COLLECTION]
        analysis_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]

        files_list = []
        skipped = 0

        user_email = request.user.email if request.user.is_authenticated else None
        user_name = request.user.username if request.user.is_authenticated else None

        for filepath, file_content in files_data:
            try:
                file_info = self._save_single_file(
                    collection=collection,
                    analysis_collection=analysis_collection,
                    filepath=filepath,
                    content=file_content,
                    project_id=project_id,
                    project_name=project_name,
                    version_number=version_number,
                    user_email=user_email,
                    user_name=user_name,
                )
                files_list.append(file_info)
            except Exception as e:
                logger.error(f"[FOLDER-UPLOAD] Failed to save {filepath}: {e}")
                skipped += 1

        return files_list, skipped

    def _save_single_file(
        self, collection, analysis_collection,
        filepath, content, project_id, project_name,
        version_number, user_email, user_name
    ):
        """
        يحفظ ملف واحد ويرجع الـ file_id.
        Content Addressing: لو الملف موجود بنفس الـ hash → يُعيد الـ id بدون حفظ جديد.
        """
        # 1. حساب الـ hash
        file_hash = hashlib.md5(content.encode()).hexdigest()

        # 2. Content Addressing — هل الملف موجود بنفس المشروع؟
        existing = collection.find_one({
            'file_hash': file_hash,
            'source_project_id': project_id
        })
        if existing:
            logger.info(f"[FOLDER-UPLOAD] Reusing: {filepath} (id={existing['_id']})")
            return {
                "file_id":       str(existing['_id']),
                "filename":      os.path.basename(filepath),
                "filepath":      filepath,
                "file_type":     existing.get('file_type', 'unknown'),
                "version_number": existing.get('version_number', version_number),
            }

        # 3. نوع الملف من الامتداد
        ext = os.path.splitext(filepath)[1].lower()
        file_type = EXTENSION_MAP.get(ext, 'unknown')
        basename = os.path.basename(filepath)

        # 4. حفظ المحتوى في GridFS
        gridfs_id = save_to_gridfs(
            content=content,
            filename=basename,
            metadata={
                'project_id':   project_id,
                'filepath':     filepath,
                'file_type':    file_type,
                'file_hash':    file_hash,
                'version':      version_number,
            }
        )

        # 5. إنشاء CodeFile في MongoDB
        code_file = CodeFile(
            filename=basename,
            file_type=file_type,
            file_hash=file_hash,
            gridfs_id=gridfs_id,
            file_size=len(content.encode('utf-8')),
            source_project_id=project_id,
            project_name=project_name,
            version_number=version_number,
            user_email=user_email,
            user_name=user_name,
            analysis_status="PENDING",
        )

        # حفظ الـ filepath الكامل كـ field إضافي
        data_to_insert = code_file.dict(by_alias=True, exclude_unset=True)
        data_to_insert['filepath'] = filepath  # src/utils.py
        if '_id' in data_to_insert and data_to_insert['_id'] is None:
            del data_to_insert['_id']

        result = collection.insert_one(data_to_insert)
        file_id = str(result.inserted_id)

        logger.info(f"[FOLDER-UPLOAD] Saved: {filepath} (id={file_id})")

        # 6. تشغيل التحليل
        analyze_code_file_task.delay(file_id)

        return {
            "file_id":        file_id,
            "filename":       basename,
            "filepath":       filepath,
            "file_type":      file_type,
            "version_number": version_number,
        }