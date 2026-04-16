from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core_ai.celery_tasks.conflict_tasks import analyze_conflict_task
from rest_framework.permissions import AllowAny

class ConflictAnalysisView(APIView):
    permission_classes = [AllowAny]  # السماح للخدمات الداخلية بالوصول

    def post(self, request):
        data = request.data
        
        # ✅ تحسين: Validation للـ Input
        analysis_type = data.get("analysis_type")
        
        if analysis_type == "code_vs_code" and not data.get("analysis_b"):
            return Response(
                {"error": "analysis_b is required for code_vs_code analysis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if analysis_type == "code_vs_doc" and not data.get("explanation"):
            return Response(
                {"error": "explanation is required for code_vs_doc analysis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        task = analyze_conflict_task.delay(
            project_id=data["project_id"],
            analysis_type=analysis_type,
            analysis_a=data["analysis_a"],
            analysis_b=data.get("analysis_b"),
            explanation=data.get("explanation")
        )

        return Response({"task_id": task.id, "status": "started"}, status=status.HTTP_202_ACCEPTED)