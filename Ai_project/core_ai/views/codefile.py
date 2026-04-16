from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core_ai.serializers.codefile import CodeFileSerializer
from core_ai.models.codefile import CodeFile, PyObjectId
from core_ai.mongo_utils import get_mongo_db
from core_ai.celery_tasks.analyze_task import analyze_code_file_task
from django.conf import settings
from bson.objectid import ObjectId
import logging

try:
    from core_ai.analysis.language_detector import detect_language
    LANGUAGE_DETECTOR_AVAILABLE = True
except ImportError:
    LANGUAGE_DETECTOR_AVAILABLE = False

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
class CodeFileViewSet(viewsets.ViewSet):
    serializer_class = CodeFileSerializer

    def get_collection(self):
        db = get_mongo_db()
        if  db is None:
            raise Exception("Failed to establish connection with MongoDB.")
        return db[settings.CODE_FILES_COLLECTION]

    def list(self, request):
        try:
            collection = self.get_collection()
            code_files_data = list(collection.find())
            code_files = [CodeFile(**self._prepare_data_for_pydantic(data)) for data in code_files_data]
            serializer = CodeFileSerializer(code_files, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing code files: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        logger.info("--- [CF-CREATE] Starting CodeFile creation ---")

        serializer = CodeFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data.copy()

        if 'uploaded_file' in validated_data and validated_data['uploaded_file']:
            uploaded_file = validated_data.pop('uploaded_file')

            try:
                file_content = uploaded_file.read().decode('utf-8')
                validated_data['content'] = file_content
                logger.info(f"--- [CF-CREATE] File content loaded, size: {len(file_content)} chars ---")

                # ✅ Auto-detect language from filename + content (override client-sent value)
                if LANGUAGE_DETECTOR_AVAILABLE:
                    detected_lang = detect_language(file_content, uploaded_file.name)
                    validated_data['file_type'] = detected_lang
                    logger.info(f"--- [CF-CREATE] Language auto-detected: {detected_lang} ---")
            except Exception as e:
                logger.error(f"--- [CF-CREATE] Failed to read file content: {e} ---")
                return Response({"error": f"Failed to read file content: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # احسب MD5 hash للملف للتحقق من التكرار
        import hashlib
        file_hash = hashlib.md5(validated_data['content'].encode()).hexdigest()
        validated_data['file_hash'] = file_hash
        logger.info(f"--- [CF-CREATE] File hash calculated: {file_hash} ---")

        # إضافة بيانات المستخدم
        if request.user.is_authenticated:
            validated_data['user_email'] = request.user.email
            validated_data['user_name'] = request.user.username
            logger.info(f"--- [CF-CREATE] User info added: {request.user.email} ---")

        try:
            logger.info("--- [CF-CREATE] Attempting to get MongoDB collection ---")
            collection = self.get_collection()

            if collection is None:
                logger.error("--- [CF-CREATE] MongoDB collection is None! ---")
                raise Exception("MongoDB collection object is missing.")

            # التحقق من وجود ملف بنفس الـ hash
            existing_file = collection.find_one({"file_hash": file_hash})
            if existing_file:
                logger.info(f"--- [CF-CREATE] File with same hash already exists: {existing_file['_id']} ---")
                
                # تحقق إذا كان هناك تحليل موجود لهذا الملف
                db = get_mongo_db()
                analysis_results_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]
                existing_analysis = analysis_results_collection.find_one({
                    "code_file_id": existing_file['_id'],
                    "status": "COMPLETED"
                })
                
                if not existing_analysis:
                    # لا يوجد تحليل - شغل Celery task للملف الموجود
                    logger.info(f"--- [CF-CREATE] No analysis found, triggering analysis ---")
                    analyze_code_file_task.delay(str(existing_file['_id']))  # ✅ استخدام الجديد
                else:
                    logger.info(f"--- [CF-CREATE] Analysis already exists ---")
                
                # ارجع نجاح مع معلومات الملف الموجود
                existing_file_data = CodeFile(**self._prepare_data_for_pydantic(existing_file))
                serializer = CodeFileSerializer(existing_file_data)
                return Response(serializer.data, status=status.HTTP_200_OK)

            code_file_instance = CodeFile(**validated_data)
            
            data_to_insert = code_file_instance.dict(by_alias=True, exclude_unset=True)
            if '_id' in data_to_insert and data_to_insert['_id'] is None:
                del data_to_insert['_id']
            
            logger.info(f"--- [CF-CREATE] Inserting new code file ---")
            result = collection.insert_one(data_to_insert)
            logger.info(f"--- [CF-CREATE] MongoDB insert successful. ID: {result.inserted_id} ---")
            
            code_file_instance.id = result.inserted_id
            serializer = CodeFileSerializer(code_file_instance)
            
            logger.info("--- [CF-CREATE] Launching Celery task ---")
            analyze_code_file_task.delay(str(result.inserted_id))  # ✅ استخدام الجديد
            
            logger.info("--- [CF-CREATE] Returning 201 response ---")

            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            logger.error(f"--- [CF-CREATE] FATAL EXCEPTION: {e}")
            logger.error(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        try:
            collection = self.get_collection()
            code_file_data = collection.find_one({"_id": ObjectId(pk)})
            if not code_file_data:
                return Response(status=status.HTTP_404_NOT_FOUND)
            code_file = CodeFile(**self._prepare_data_for_pydantic(code_file_data))
            serializer = CodeFileSerializer(code_file)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving code file {pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        try:
            collection = self.get_collection()
            code_file_data = collection.find_one({"_id": ObjectId(pk)})
            if not code_file_data:
                return Response(status=status.HTTP_404_NOT_FOUND)
            
            code_file_instance = CodeFile(**self._prepare_data_for_pydantic(code_file_data))
            
            serializer = CodeFileSerializer(code_file_instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            updated_data = serializer.validated_data
            
            collection.update_one({"_id": ObjectId(pk)}, {"$set": updated_data})
            
            updated_code_file_data = collection.find_one({"_id": ObjectId(pk)})
            updated_code_file_instance = CodeFile(**self._prepare_data_for_pydantic(updated_code_file_data))
            
            return Response(CodeFileSerializer(updated_code_file_instance).data)
        except Exception as e:
            logger.error(f"Error updating code file {pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        try:
            collection = self.get_collection()
            result = collection.delete_one({"_id": ObjectId(pk)})
            if result.deleted_count == 0:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting code file {pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        try:
            collection = self.get_collection()
            
            # Try to convert pk to ObjectId, if fails, search by source_project_id instead
            try:
                object_id = ObjectId(pk)
                code_file_data = collection.find_one({"_id": object_id})
                code_file_id_for_analysis = object_id
            except:
                # pk is not a valid ObjectId, treat it as source_project_id (UUID)
                code_file_data = collection.find_one({"source_project_id": pk})
                if code_file_data and "_id" in code_file_data:
                    code_file_id_for_analysis = code_file_data["_id"]
                else:
                    return Response({"error": f"Code file not found for project_id: {pk}"}, status=status.HTTP_404_NOT_FOUND)
            if not code_file_data:
                return Response(status=status.HTTP_404_NOT_FOUND)

            # التحقق من وجود تحليل مكتمل بالفعل
            db = get_mongo_db()
            analysis_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]
            existing_analysis = analysis_collection.find_one({
                "code_file_id": code_file_id_for_analysis, 
                "status": "COMPLETED"
            })
            
            if existing_analysis:
                logger.info(f"--- [CF-ANALYZE] Analysis already exists for file {pk} ---")
                return Response({
                    "message": f"Analysis already exists for this file.",
                    "analysis_id": str(existing_analysis['_id'])
                }, status=status.HTTP_200_OK)

            # التحقق من وجود تحليل قيد التنفيذ
            in_progress_analysis = analysis_collection.find_one({
                "code_file_id": code_file_id_for_analysis, 
                "status": "IN_PROGRESS"
            })
            
            if in_progress_analysis:
                logger.info(f"--- [CF-ANALYZE] Analysis already in progress for file {pk} ---")
                return Response({
                    "message": f"Analysis is already in progress for this file."
                }, status=status.HTTP_202_ACCEPTED)

            collection.update_one(
                {"_id": code_file_id_for_analysis}, 
                {"$set": {"analysis_status": "IN_PROGRESS"}}
            )

            analyze_code_file_task.delay(str(code_file_id_for_analysis))  # ✅ استخدام الجديد
            
            return Response({
                "message": f"Analysis for CodeFile {pk} started."
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Error starting analysis for file {pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='by-project')
    def by_project(self, request):
        """
        جلب ملفات الكود المتعلقة بمشروع معين
        URL: /api/code-files/by-project/?project_id={project_id}
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({
                "error": "project_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            collection = self.get_collection()
            code_files_data = list(collection.find({"source_project_id": project_id}))

            if not code_files_data:
                return Response({
                    "message": f"No code files found for project {project_id}",
                    "code_files": []
                }, status=status.HTTP_200_OK)

            code_files = [CodeFile(**self._prepare_data_for_pydantic(data)) for data in code_files_data]
            serializer = CodeFileSerializer(code_files, many=True)

            return Response({
                "project_id": project_id,
                "total_files": len(code_files),
                "code_files": serializer.data
            })

        except Exception as e:
            logger.error(f"Error fetching files for project {project_id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _prepare_data_for_pydantic(self, data):
        """
        Helper to convert MongoDB _id to 'id' for Pydantic models.
        Also converts ObjectId values within the document.
        """
        if '_id' in data:
            data['id'] = data.pop('_id')
        
        def convert_object_ids(obj):
            if isinstance(obj, dict):
                return {k: convert_object_ids(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_object_ids(elem) for elem in obj]
            elif isinstance(obj, ObjectId):
                return PyObjectId(obj)
            return obj
        
        return convert_object_ids(data)