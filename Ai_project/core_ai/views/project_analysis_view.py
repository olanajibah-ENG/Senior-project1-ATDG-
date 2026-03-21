from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from core_ai.mongo_utils import get_mongo_db
from core_ai.celery_tasks.analyze_project_task import analyze_project_task


class AnalyzeProjectView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [AllowAny]

    def post(self, request):
        project_id = request.data.get('project_id')
        if not project_id:
            return Response(
                {"error": "project_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        task = analyze_project_task.delay(project_id)

        return Response({
            "message":    "Analysis started",
            "project_id": project_id,
            "task_id":    task.id
        }, status=status.HTTP_202_ACCEPTED)

    def get(self, request):
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "project_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        db     = get_mongo_db()
        result = db['project_analysis_results'].find_one(
            {"project_id": project_id},
            sort=[("created_at", -1)]
        )

        if not result:
            return Response({"status": "PENDING"}, status=status.HTTP_404_NOT_FOUND)

        result['_id'] = str(result['_id'])
        return Response(result)
