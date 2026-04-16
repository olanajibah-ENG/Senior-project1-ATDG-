"""
views/folder_upload.py
======================
FolderUploadView — رفع مجلدات وملفات متعددة مع دعم versioning
"""

import io
import os
import uuid
import hashlib
import zipfile
import logging
import re
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

# ====================== LANGUAGE DETECTION ======================
def detect_language_robust(content: str, filename: str = "") -> str:
    """كشف لغة البرمجة بدقة عالية"""
    if not content or len(content.strip()) < 5:
        return "text"

    ext = os.path.splitext(filename.lower())[-1]

    # أولوية قصوى للامتداد
    ext_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
        '.java': 'java', '.cs': 'c_sharp', '.cpp': 'cpp', '.c': 'c', '.go': 'go',
        '.rb': 'ruby', '.php': 'php', '.kt': 'kotlin', '.rs': 'rust'
    }

    if ext in ext_map:
        return ext_map[ext]

    # Heuristics
    lower = content.lower()
    if re.search(r'using\s+System|namespace\s+\w+|public class|class \w+ :', lower):
        return 'c_sharp'
    if re.search(r'#include|std::|template<|cout|cin|vector<', lower):
        return 'cpp'
    if re.search(r'def \w+\s*\(|import |from .* import|async def|class \w+:|if __name__ ==', lower):
        return 'python'
    if re.search(r'function |const |let |=>|export |async function|console\.', lower):
        return 'javascript'
    if '<?php' in lower or re.search(r'function \w+\s*\(', lower) and '$' in lower[:600]:
        return 'php'
    if re.search(r'fn |let |mut |impl |struct |trait |pub |mod ', lower):
        return 'rust'

    return 'text'


# امتدادات مدعومة
SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.java', '.cs', '.cpp', '.c', 
                       '.go', '.rb', '.php', '.kt', '.rs'}

IGNORED_PREFIXES = ('__MACOSX', '.', '__pycache__', '.git')
IGNORED_EXTENSIONS = ('.pyc', '.class', '.exe', '.dll', '.so', '.o', '.git', '.md', '.txt')
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

        upm_project_id = request.data.get('upm_project_id', '').strip() or project_name

        try:
            files_data = self._extract_files(request, project_name)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] Extraction error: {e}")
            return Response({"error": "Failed to process uploaded files"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not files_data:
            return Response({
                "error": "No supported files found",
                "supported_extensions": list(SUPPORTED_EXTENSIONS)
            }, status=status.HTTP_400_BAD_REQUEST)

        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        version_number, prev_file_ids = self._get_next_version(db, upm_project_id)
        logger.info(f"[FOLDER-UPLOAD] project_id={upm_project_id}, version={version_number}, prev_files={len(prev_file_ids)}")

        try:
            file_ids_list, skipped = self._save_files(
                db, files_data, upm_project_id, project_name, version_number, request
            )
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] Save error: {e}")
            return Response({"error": f"Failed to save files: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        self._save_project_version(
            db, upm_project_id, project_name, version_number,
            file_ids_list, prev_file_ids, request
        )

        logger.info(f"[FOLDER-UPLOAD] Completed — version={version_number}, saved={len(file_ids_list)}, skipped={skipped}")

        return Response({
            "project_id":     upm_project_id,
            "project_name":   project_name,
            "version_number": version_number,
            "file_count":     len(file_ids_list),
            "file_ids":       [f["file_id"] for f in file_ids_list],
            "files":          file_ids_list,
            "skipped":        skipped,
        }, status=status.HTTP_201_CREATED)

    # ── Versioning ─────────────────────────────────────────────────────────────
    def _get_next_version(self, db, upm_project_id):
        """
        يرجع (version_number, prev_file_ids).
        prev_file_ids = كل file_ids من آخر إصدار سابق (لنضمها لاحقاً).
        """
        collection   = db[PROJECT_VERSIONS_COLLECTION]
        last_version = collection.find_one(
            {"project_id": upm_project_id},
            sort=[("version_number", -1)]
        )
        if last_version:
            v            = last_version["version_number"] + 1
            prev_ids     = last_version.get("file_ids", [])
            logger.info(f"[FOLDER-UPLOAD] Existing project → version {v}")
            return v, prev_ids
        logger.info("[FOLDER-UPLOAD] New project → version 1")
        return 1, []

    def _save_project_version(self, db, project_id, project_name,
                               version_number, new_files_list, prev_file_ids, request):
        """
        يحفظ project_version document بـ:
          - file_ids    : كل IDs (قديمة + جديدة/معدّلة) — للـ tree
          - file_changes: تفاصيل كل ملف + إشارة التغيير — للـ UI

        منطق الدمج:
          1. الملفات الجديدة/المعدّلة (file_ids_list من الرفع الحالي)
             → status = "new" أو "modified"
          2. الملفات القديمة من prev_file_ids اللي مش موجودة في الرفع الحالي
             → status = "unchanged"
        """
        collection = db[PROJECT_VERSIONS_COLLECTION]
        code_files  = db[settings.CODE_FILES_COLLECTION]
        user_email  = request.user.email if request.user.is_authenticated else request.data.get('user_email')

        # الـ file_ids الجديدة/المعدّلة من الرفع الحالي
        current_ids  = {f["file_id"] for f in new_files_list}

        # ── بناء file_changes ───────────────────────────────────────────────
        file_changes = []

        # 1. الملفات الجديدة أو المعدّلة
        for f in new_files_list:
            # إذا كان الـ version_number في الملف يساوي الإصدار الحالي → جديد أو معدّل
            # لو version_number أقل → unchanged (ملف قديم ما اتغيّر، جاء من content addressing)
            if f.get("version_number") == version_number:
                # ملف جديد أو معدّل — نحدد بالبحث في prev_file_ids
                if f["file_id"] in set(str(x) for x in prev_file_ids):
                    change_status = "modified"  # كان موجود بنفس الـ ID → ما يصير، لكن احتياطاً
                else:
                    change_status = "new" if version_number == 1 else "new_or_modified"
            else:
                # content addressing رجّع ملف قديم → unchanged
                change_status = "unchanged"

            file_changes.append({
                "file_id"       : f["file_id"],
                "filename"      : f["filename"],
                "filepath"      : f["filepath"],
                "file_type"     : f["file_type"],
                "version_number": f.get("version_number", version_number),
                "status"        : change_status,
            })

        # 2. الملفات من الإصدار السابق اللي مش في الرفع الحالي → unchanged
        #    (ملفات ما رُفعت هاي المرة — بس لازم تظهر في الإصدار الجديد)
        prev_ids_not_in_current = [
            pid for pid in prev_file_ids
            if str(pid) not in current_ids
        ]

        if prev_ids_not_in_current:
            prev_obj_ids = []
            for pid in prev_ids_not_in_current:
                try:
                    prev_obj_ids.append(ObjectId(str(pid)))
                except:
                    pass

            unchanged_docs = list(code_files.find(
                {"_id": {"$in": prev_obj_ids}},
                {"_id": 1, "filename": 1, "filepath": 1, "file_type": 1, "version_number": 1}
            ))

            for doc in unchanged_docs:
                file_changes.append({
                    "file_id"       : str(doc["_id"]),
                    "filename"      : doc.get("filename", ""),
                    "filepath"      : doc.get("filepath", doc.get("filename", "")),
                    "file_type"     : doc.get("file_type", "unknown"),
                    "version_number": doc.get("version_number", 1),
                    "status"        : "unchanged",
                })

        # كل الـ file_ids المجمّعة (جديدة + قديمة)
        all_file_ids = list(current_ids) + [
            str(pid) for pid in prev_file_ids if str(pid) not in current_ids
        ]

        collection.insert_one({
            "project_id":     project_id,
            "project_name":   project_name,
            "version_number": version_number,
            "file_ids":       all_file_ids,      # كل الملفات
            "file_changes":   file_changes,       # مع إشارة التغيير
            "total_files":    len(all_file_ids),
            "new_files":      sum(1 for f in file_changes if f["status"] != "unchanged"),
            "unchanged_files": sum(1 for f in file_changes if f["status"] == "unchanged"),
            "user_email":     user_email,
            "created_at":     datetime.utcnow(),
        })
        logger.info(
            f"[FOLDER-UPLOAD] Version {version_number} saved: "
            f"total={len(all_file_ids)}, "
            f"new/modified={sum(1 for f in file_changes if f['status'] != 'unchanged')}, "
            f"unchanged={sum(1 for f in file_changes if f['status'] == 'unchanged')}"
        )

    # ── File Extraction ────────────────────────────────────────────────────────
    def _extract_files(self, request, project_name):
        all_files = (
            list(request.FILES.getlist('file')) +
            list(request.FILES.getlist('files')) +
            list(request.FILES.getlist('folder'))
        )
        if not all_files:
            raise ValueError("No files received. Send 'files' (multiple) or 'file' (single/ZIP).")

        if len(all_files) == 1 and all_files[0].name.lower().endswith('.zip'):
            return self._extract_from_zip(all_files[0])

        archives = [f for f in all_files if f.name.lower().endswith('.zip')]
        if archives:
            result = []
            for f in archives:
                result.extend(self._extract_from_zip(f))
            if result:
                return result

        return self._extract_from_files(all_files, project_name)

    def _extract_from_zip(self, uploaded_file):
        """استخراج من ZIP مع قراءة مرة واحدة"""
        result = []
        try:
            raw_data = uploaded_file.read()   # قراءة مرة واحدة
            with zipfile.ZipFile(io.BytesIO(raw_data)) as zf:
                for entry in zf.namelist():
                    if entry.endswith('/') or any(entry.startswith(p) for p in IGNORED_PREFIXES):
                        continue
                    ext = os.path.splitext(entry)[1].lower()
                    if ext in IGNORED_EXTENSIONS:
                        continue
                    try:
                        content = zf.read(entry).decode('utf-8', errors='ignore')
                        result.append((entry, content))
                    except Exception as e:
                        logger.warning(f"[FOLDER-UPLOAD] Skipping {entry}: {e}")
        except zipfile.BadZipFile:
            raise ValueError("Invalid ZIP file.")
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] ZIP extraction error: {e}")
            raise ValueError("Failed to extract ZIP file")

        logger.info(f"[FOLDER-UPLOAD] Extracted {len(result)} files from ZIP")
        return result

    def _extract_from_files(self, files, project_name):
        result = []
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if ext in IGNORED_EXTENSIONS:
                continue

            try:
                content = f.read().decode('utf-8', errors='ignore')
                filepath = f.name if os.path.dirname(f.name) else f"{project_name}/{f.name}"
                result.append((filepath, content))
            except Exception as e:
                logger.warning(f"[FOLDER-UPLOAD] Skipping {f.name}: {e}")
        return result

    # ── Save Files ─────────────────────────────────────────────────────────────
    def _save_files(self, db, files_data, project_id, project_name, version_number, request):
        collection          = db[settings.CODE_FILES_COLLECTION]
        analysis_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]
        files_list          = []
        skipped             = 0
        user_email = request.user.email if request.user.is_authenticated else request.data.get('user_email')
        user_name  = request.user.username if request.user.is_authenticated else None

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
        """
        Content Addressing:
        - لو الملف موجود بنفس hash ونفس المشروع → يرجع نفس الـ id (unchanged)
          مع version_number القديم (ما يتحدث) — هيك نعرف إنه unchanged
        - لو hash جديد → يُحفظ كـ document جديد بـ version_number الحالي
        """
        file_hash = hashlib.md5(content.encode()).hexdigest()

        existing = collection.find_one({'file_hash': file_hash, 'source_project_id': project_id})
        if existing:
            logger.info(f"[FOLDER-UPLOAD] Reusing (unchanged): {filepath}")
            return {
                "file_id":        str(existing['_id']),
                "filename":       os.path.basename(filepath),
                "filepath":       filepath,
                "file_type":      existing.get('file_type', 'unknown'),
                "version_number": existing.get('version_number', 1),  # الإصدار القديم الأصلي
            }

        # === الكشف عن اللغة ===
        file_type = detect_language_robust(content, filepath)
        basename = os.path.basename(filepath)

        gridfs_id = save_to_gridfs(
            content=content,
            filename=basename,
            metadata={
                'project_id': project_id, 'filepath': filepath,
                'file_type':  file_type,  'file_hash': file_hash,
                'version':    version_number,
            }
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

        result  = collection.insert_one(data_to_insert)
        file_id = str(result.inserted_id)
        logger.info(f"[FOLDER-UPLOAD] Saved new: {filepath} → {file_type} v{version_number}")

        analyze_code_file_task.delay(file_id)

        return {
            "file_id":        file_id,
            "filename":       basename,
            "filepath":       filepath,
            "file_type":      file_type,
            "version_number": version_number,  # الإصدار الحالي
        }