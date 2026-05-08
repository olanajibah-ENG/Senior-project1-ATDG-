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


class ProjectClassDiagramView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [AllowAny]

    def get(self, request, project_id):
        if not project_id:
            return Response({"error": "project_id required"}, status=status.HTTP_400_BAD_REQUEST)

        db = get_mongo_db()

        # جلب نتيجة تحليل المشروع
        project_result = db['project_analysis_results'].find_one(
            {"project_id": project_id},
            sort=[("created_at", -1)]
        )

        if not project_result:
            return Response({"error": "Project analysis not found. Run analyze-project first."}, status=status.HTTP_404_NOT_FOUND)

        if project_result.get('status') not in ('COMPLETED', 'COMPLETED_WITH_ERRORS'):
            return Response({
                "error": f"Project analysis not completed yet. Status: {project_result.get('status')}",
            }, status=status.HTTP_400_BAD_REQUEST)

        # جلب analysis_ids وتوليد المخطط الموحد من نتائج كل ملف
        from bson import ObjectId
        analysis_ids = project_result.get('analysis_ids', [])
        
        unified_classes = []
        unified_relationships = []
        all_potential_relationships = []
        seen_classes = set()

        for aid in analysis_ids:
            try:
                oid = ObjectId(aid)
                analysis = db['analysis_results'].find_one({"_id": oid})
                if not analysis:
                    continue
                diagram = analysis.get('class_diagram_data', {})
                if not diagram or not isinstance(diagram, dict):
                    continue

                # جلب filepath من code_file
                filepath = ""
                code_file_id = analysis.get('code_file_id')
                if code_file_id:
                    cf = db['code_files'].find_one({"_id": code_file_id})
                    if cf:
                        filepath = cf.get('filepath', cf.get('filename', ''))

                for cls in diagram.get('classes', []):
                    cls_name = cls.get('name', '')
                    if cls_name and cls_name not in seen_classes:
                        cls_copy = dict(cls)
                        if 'filepath' not in cls_copy:
                            cls_copy['filepath'] = filepath
                        unified_classes.append(cls_copy)
                        seen_classes.add(cls_name)

                # تجميع كل العلاقات الممكنة (بما فيها التي تشير لملفات أخرى)
                for rel in diagram.get('relationships', []):
                    all_potential_relationships.append(rel)

            except Exception:
                continue

        # فلترة العلاقات: ابقِ فقط العلاقات التي تشير إلى كلاسات موجودة فعلياً في المشروع
        for rel in all_potential_relationships:
            target = rel.get('to', '')
            # إبقاء الوراثة من ABC أو أنواع تقنية محددة، أو كلاسات موجودة في المشروع
            if target in seen_classes or target in ['ABC', 'object', 'Exception']:
                if rel not in unified_relationships:
                    unified_relationships.append(rel)

        return Response({
            "project_id": project_id,
            "status": "success",
            "total_classes": len(unified_classes),
            "project_class_diagram": {
                "classes": unified_classes,
                "relationships": unified_relationships
            }
        }, status=status.HTTP_200_OK)

