import json
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core_ai.serializers.analysis import  AnalysisJobSerializer, AnalysisResultSerializer
from core_ai.models.analysis import  AnalysisJob, AnalysisResult, PyObjectId
from core_ai.models.ai_task import AITask
from core_ai.mongo_utils import get_mongo_db
from django.conf import settings
from bson.objectid import ObjectId
from rest_framework.permissions import AllowAny
from core_ai.celery_tasks.analyze_task import analyze_code_file_task


@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
def start_analysis(request):
    """
    Start a specific analysis for a code file
    Body: { code_file_id: string }
    """
    try:
        code_file_id = request.data.get('code_file_id')
        
        if not code_file_id:
            return Response(
                {"error": "code_file_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start Celery task
        task = analyze_code_file_task.delay(code_file_id)
        
        return Response({
            "task_id": task.id,
            "message": f"Analysis started for code file {code_file_id}"
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
def get_task_status(request, task_id):
    """
    Get the status of a specific task by task_id
    """
    try:
        task = AITask.get_by_task_id(task_id)
        
        if not task:
            return Response(
                {"error": "Task not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        response_data = {
            "task_id": task.task_id,
            "status": task.status,
            "analysis_id": str(task.analysis_id),  # Convert ObjectId to string
            "exp_type": task.exp_type,
            "explain_level": task.explain_level,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "result": task.result,
            "error": task.error
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
class AnalysisJobViewSet(viewsets.ViewSet):
    serializer_class = AnalysisJobSerializer

    def get_collection(self):
        db = get_mongo_db()
        if db is None:
            raise Exception("Could not connect to MongoDB")
        return db[settings.ANALYSIS_JOBS_COLLECTION] # سنعرف هذا في settings.py

    def list(self, request):
        try:
            collection = self.get_collection()
            jobs_data = list(collection.find())
            jobs = [AnalysisJob(**self._prepare_data_for_pydantic(data)) for data in jobs_data]
            serializer = AnalysisJobSerializer(jobs, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        serializer = AnalysisJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            collection = self.get_collection()
            job_instance = AnalysisJob(**serializer.validated_data)
            
            data_to_insert = job_instance.dict(by_alias=True, exclude_unset=True)
            if '_id' in data_to_insert and data_to_insert['_id'] is None:
                del data_to_insert['_id']
            
            result = collection.insert_one(data_to_insert)
            
            job_instance.id = result.inserted_id
            serializer = AnalysisJobSerializer(job_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        try:
            collection = self.get_collection()
            job_data = collection.find_one({"_id": ObjectId(pk)})
            if not job_data:
                return Response(status=status.HTTP_404_NOT_FOUND)
            job = AnalysisJob(**self._prepare_data_for_pydantic(job_data))
            serializer = AnalysisJobSerializer(job)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        try:
            collection = self.get_collection()
            job_data = collection.find_one({"_id": ObjectId(pk)})
            if not job_data:
                return Response(status=status.HTTP_404_NOT_FOUND)
            
            job_instance = AnalysisJob(**self._prepare_data_for_pydantic(job_data))
            
            serializer = AnalysisJobSerializer(job_instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            updated_data = serializer.validated_data
            
            collection.update_one({"_id": ObjectId(pk)}, {"$set": updated_data})
            
            updated_job_data = collection.find_one({"_id": ObjectId(pk)})
            updated_job_instance = AnalysisJob(**self._prepare_data_for_pydantic(updated_job_data))
            
            return Response(AnalysisJobSerializer(updated_job_instance).data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        try:
            collection = self.get_collection()
            result = collection.delete_one({"_id": ObjectId(pk)})
            if result.deleted_count == 0:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def _prepare_data_for_pydantic(self, data):
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


@method_decorator(csrf_exempt, name='dispatch')
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
class AnalysisResultViewSet(viewsets.ViewSet):
    serializer_class = AnalysisResultSerializer

    @action(detail=True, methods=['get'])
    def class_diagram(self, request, pk=None):
        """الحصول على بيانات class diagram فقط"""
        try:
            collection = self.get_collection()
            result_data = collection.find_one({"_id": ObjectId(pk)})
            if not result_data:
                return Response(status=status.HTTP_404_NOT_FOUND)

            # Return class_diagram_data as-is (JSON object) - let frontend handle conversion
            class_diagram_data = result_data.get('class_diagram_data', {})
            return Response({"class_diagram_data": class_diagram_data})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_collection(self):
        db = get_mongo_db()
        if db is None:
            raise Exception("Could not connect to MongoDB")
        return db[settings.ANALYSIS_RESULTS_COLLECTION] # سنعرف هذا في settings.py

    def list(self, request):
        try:
            collection = self.get_collection()

            # Filter by code_file_id if provided
            query = {}
            code_file_id = request.query_params.get('code_file_id')
            if code_file_id:
                query['code_file_id'] = ObjectId(code_file_id)

            results_data = list(collection.find(query))
            
            # Process each result to handle class_diagram_data format
            processed_results = []
            for data in results_data:
                # Keep class_diagram_data as object - don't convert to string
                # The JSONField serializer will handle it properly
                # (Removed the string conversion logic)

                # Prepare data for Pydantic
                prepared_data = self._prepare_data_for_pydantic(data)
                try:
                    result = AnalysisResult(**prepared_data)
                    processed_results.append(result)
                except Exception as validation_error:
                    print(f"Validation error for result {data.get('_id')}: {validation_error}")
                    # Skip invalid results or handle them gracefully
                    continue
            
            serializer = AnalysisResultSerializer(processed_results, many=True)

            # Return in the format expected by frontend: {results: [...]}
            return Response({"results": serializer.data})
        except Exception as e:
            import traceback
            print("--- DEBUG: [AnalysisResultViewSet.list] FATAL EXCEPTION ---")
            print(f"Error: {e}")
            print(traceback.format_exc()) # طباعة الـ traceback الكامل
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        serializer = AnalysisResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            collection = self.get_collection()
            result_instance = AnalysisResult(**serializer.validated_data)
            
            data_to_insert = result_instance.dict(by_alias=True, exclude_unset=True)

            # Keep class_diagram_data as object - JSONField serializer will handle it
            
            if '_id' in data_to_insert and data_to_insert['_id'] is None:
                del data_to_insert['_id']
            
            result = collection.insert_one(data_to_insert)
            
            result_instance.id = result.inserted_id
            serializer = AnalysisResultSerializer(result_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def retrieve(self, request, pk=None):
        try:
            print(f"--- DEBUG: [AnalysisResultViewSet.retrieve] Fetching result with pk: {pk} ---")
            collection = self.get_collection()
            
            try:
                object_id = ObjectId(pk)
            except Exception as e:
                print(f"--- DEBUG: [AnalysisResultViewSet.retrieve] Invalid ObjectId: {pk}, Error: {e} ---")
                return Response({"error": f"Invalid ID format: {pk}"}, status=status.HTTP_400_BAD_REQUEST)
            
            result_data = collection.find_one({"_id": object_id})
            if not result_data:
                print(f"--- DEBUG: [AnalysisResultViewSet.retrieve] No result found for ID: {pk} ---")
                return Response({"error": f"No result found for ID: {pk}"}, status=status.HTTP_404_NOT_FOUND)
            
            print(f"--- DEBUG: [AnalysisResultViewSet.retrieve] Found result data: {result_data.get('status')} ---")
            
            try:
                prepared_data = self._prepare_data_for_pydantic(result_data)
                print(f"--- DEBUG: [AnalysisResultViewSet.retrieve] Data prepared successfully ---")
                result = AnalysisResult(**prepared_data)
                serializer = AnalysisResultSerializer(result)
                print(f"--- DEBUG: [AnalysisResultViewSet.retrieve] Returning serialized data ---")
                return Response(serializer.data)
            except Exception as pydantic_error:
                print(f"--- DEBUG: [AnalysisResultViewSet.retrieve] Pydantic validation error: {pydantic_error} ---")
                print(f"--- DEBUG: [AnalysisResultViewSet.retrieve] Prepared data keys: {prepared_data.keys() if 'prepared_data' in locals() else 'N/A'} ---")
                import traceback
                print(traceback.format_exc())
                return Response({"error": f"Validation error: {str(pydantic_error)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(f"--- DEBUG: [AnalysisResultViewSet.retrieve] FATAL EXCEPTION: {e} ---")
            import traceback
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def update(self, request, pk=None):
        try:
            collection = self.get_collection()
            result_data = collection.find_one({"_id": ObjectId(pk)})
            if not result_data:
                return Response(status=status.HTTP_404_NOT_FOUND)
            
            result_instance = AnalysisResult(**self._prepare_data_for_pydantic(result_data))
            
            serializer = AnalysisResultSerializer(result_instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            updated_data = serializer.validated_data
            
            collection.update_one({"_id": ObjectId(pk)}, {"$set": updated_data})
            
            updated_result_data = collection.find_one({"_id": ObjectId(pk)})
            updated_result_instance = AnalysisResult(**self._prepare_data_for_pydantic(updated_result_data))
            
            return Response(AnalysisResultSerializer(updated_result_instance).data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def destroy(self, request, pk=None):
        try:
            collection = self.get_collection()
            result = collection.delete_one({"_id": ObjectId(pk)})
            if result.deleted_count == 0:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _prepare_data_for_pydantic(self, data):
        if '_id' in data:
            data['id'] = data.pop('_id')

        # البيانات الآن تُحفظ كـ Dict مباشرة، لا حاجة لتحويل JSON

        def convert_object_ids(obj):
            if isinstance(obj, dict):
                return {k: convert_object_ids(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_object_ids(elem) for elem in obj]
            elif isinstance(obj, ObjectId):
                return PyObjectId(obj)
            return obj
        return convert_object_ids(data)
