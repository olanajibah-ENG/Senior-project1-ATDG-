from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core_ai.views.codefile import CodeFileViewSet
from core_ai.views.analysis import (
    AnalysisJobViewSet, 
    AnalysisResultViewSet,
    start_analysis,
    get_task_status
)
from core_ai.views.explanation_views import AIExplanationViewSet
from core_ai.views.export_views import (
    export_doc,
    generate_document,
    list_generated_files_view,
    download_generated_file
)

print("CORE_AI URLS.PY LOADED!")
print("UNIFIED EXPORT ENDPOINTS LOADED!")

router = DefaultRouter()
router.register(r'codefiles', CodeFileViewSet, basename='codefile')
router.register(r'analysis-jobs', AnalysisJobViewSet, basename='analysis-job')
router.register(r'analysis-results', AnalysisResultViewSet, basename='analysis-result')
router.register(r'ai-explanations', AIExplanationViewSet, basename='ai_explanations')

urlpatterns = [
    path('analyze/', start_analysis, name='start-analysis'),
    path('task-status/<str:task_id>/', get_task_status, name='task-status'),
    path('', include(router.urls)),
    path('export/<str:analysis_id>/', export_doc, name='export'),
    path('generate-document/', generate_document, name='generate-document'),
    path('generated-files/', list_generated_files_view, name='list-files'),
    path('download-generated-file/<str:file_id>/', download_generated_file, name='download-generated-file'),
]
