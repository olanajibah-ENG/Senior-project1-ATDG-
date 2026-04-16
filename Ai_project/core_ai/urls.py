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
from core_ai.views.stats_views import (
    reviewer_stats_view,
    ai_tasks_list_view
)
from core_ai.views.evaluation_views import (
    evaluate_explanation,
    get_evaluation_history,
    get_evaluation_stats,
    submit_human_review
)

from core_ai.views.folder_upload import FolderUploadView
from core_ai.views.dependency_graph_view import dependency_graph_view
from core_ai.views.context_view import cross_file_context_view
from core_ai.views.project_analysis_view import AnalyzeProjectView, ProjectClassDiagramView

# ← جديد: استيراد view شجرة المشروع ومحتوى الملف
from core_ai.views.project_tree_view import ProjectVersionsView, ProjectTreeView, FileContentView
print("CORE_AI URLS.PY LOADED!")

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
    
    path('reviewer/stats/', reviewer_stats_view, name='reviewer-stats'),
    path('reviewer/ai-tasks/', ai_tasks_list_view, name='ai-tasks-list'),
    
    # Evaluation endpoints
    path('evaluate-explanation/<str:explanation_id>/', evaluate_explanation, name='evaluate-explanation'),
    path('evaluation-history/<str:explanation_id>/', get_evaluation_history, name='evaluation-history'),
    path('evaluation-stats/', get_evaluation_stats, name='evaluation-stats'),
    path('submit-human-review/<str:explanation_id>/', submit_human_review, name='submit-human-review'),

    path('analyze-project/', AnalyzeProjectView.as_view(), name='analyze-project'),
    path('project-class-diagram/<str:project_id>/', ProjectClassDiagramView.as_view(), name='project-class-diagram'),
    path('dependency-graph/', dependency_graph_view, name='dependency-graph'),
    path('cross-file-context/', cross_file_context_view, name='cross-file-context'),
    path('upload-folder/', FolderUploadView.as_view(), name='upload-folder'),

    # ← جديد: شجرة المشروع ومحتوى الملف
    path('project-tree/<str:upm_project_id>/', ProjectTreeView.as_view(), name='project-tree'),
    path('file-content/<str:file_id>/', FileContentView.as_view(), name='file-content'),
     # الخطوة 1: جيب كل الإصدارات (عرضها للمستخدم ليختار)
    path('project-versions/<str:upm_project_id>/',      ProjectVersionsView.as_view(),  name='project-versions'),
]