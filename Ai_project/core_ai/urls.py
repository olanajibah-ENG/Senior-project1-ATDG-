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
    submit_human_review,
    get_all_explanations_with_evaluations
)
from core_ai.views.folder_upload import FolderUploadView
from core_ai.views.dependency_graph_view import dependency_graph_view
from core_ai.views.context_view import cross_file_context_view
from core_ai.views.project_analysis_view import AnalyzeProjectView, ProjectClassDiagramView
from core_ai.views.project_tree_view import ProjectVersionsView, ProjectTreeView, FileContentView
from core_ai.views.file_version_view import FileVersionsView, FileDocsView

# ── Conflict Detection Views ─────────────────────────────────────────
from core_ai.views.conflict_views import (
    ConflictDetectionView,
    ConflictStatusView,
    ConflictResultView,
    ConflictHistoryView,
)

print("CORE_AI URLS.PY LOADED!")

router = DefaultRouter()
router.register(r'codefiles',        CodeFileViewSet,       basename='codefile')
router.register(r'analysis-jobs',    AnalysisJobViewSet,    basename='analysis-job')
router.register(r'analysis-results', AnalysisResultViewSet, basename='analysis-result')
router.register(r'ai-explanations',  AIExplanationViewSet,  basename='ai_explanations')

urlpatterns = [
    # ── Analysis ────────────────────────────────────────────────────────────
    path('analyze/',                  start_analysis,  name='start-analysis'),
    path('task-status/<str:task_id>/', get_task_status, name='task-status'),
    path('', include(router.urls)),

    # ── Export / Files ───────────────────────────────────────────────────────
    path('export/<str:analysis_id>/',               export_doc,               name='export'),
    path('generate-document/',                       generate_document,        name='generate-document'),
    path('generated-files/',                         list_generated_files_view, name='list-files'),
    path('download-generated-file/<str:file_id>/',   download_generated_file,  name='download-generated-file'),

    # ── Conflict Detection ───────────────────────────────────────────────────
    path('detect-conflict/',                         ConflictDetectionView.as_view(), name='detect-conflict'),

    path('conflict-status/',                         ConflictStatusView.as_view(),    name='conflict-status'),
    path('conflict-status/<str:task_id>/',           ConflictStatusView.as_view(),    name='conflict-status-by-id'),

    path('conflict-result/<str:analysis_id>/',       ConflictResultView.as_view(),    name='conflict-result'),
    path('conflict-history/',                        ConflictHistoryView.as_view(),   name='conflict-history'),

    # ── Stats ────────────────────────────────────────────────────────────────
    path('reviewer/stats/',    reviewer_stats_view,  name='reviewer-stats'),
    path('reviewer/ai-tasks/', ai_tasks_list_view,   name='ai-tasks-list'),

    # ── Evaluation ───────────────────────────────────────────────────────────
    path('evaluate-explanation/<str:explanation_id>/',  evaluate_explanation,   name='evaluate-explanation'),
    path('evaluation-history/<str:explanation_id>/',    get_evaluation_history, name='evaluation-history'),
    path('evaluation-history/',                           get_all_explanations_with_evaluations, name='evaluation-history-all'),
    path('evaluation-stats/',                           get_evaluation_stats,   name='evaluation-stats'),
    path('submit-human-review/<str:explanation_id>/',   submit_human_review,    name='submit-human-review'),

    # ── Project Analysis ─────────────────────────────────────────────────────
    path('analyze-project/',                          AnalyzeProjectView.as_view(),          name='analyze-project'),
    path('project-class-diagram/<str:project_id>/',   ProjectClassDiagramView.as_view(),     name='project-class-diagram'),
    path('dependency-graph/',                         dependency_graph_view,                 name='dependency-graph'),
    path('cross-file-context/',                       cross_file_context_view,               name='cross-file-context'),
    path('upload-folder/',                            FolderUploadView.as_view(),            name='upload-folder'),

    # ── Project Tree & Versions ──────────────────────────────────────────────
    path('project-tree/<str:upm_project_id>/',        ProjectTreeView.as_view(),             name='project-tree'),
    path('file-content/<str:file_id>/',               FileContentView.as_view(),             name='file-content'),
    path('project-versions/<str:upm_project_id>/',    ProjectVersionsView.as_view(),         name='project-versions'),
    # ⚠️ by-path لازم يجي قبل <file_id> لأن Django يمشي بالترتيب
    path('file-versions/by-path/',                    FileVersionsView.as_view(),            name='file-versions-by-path'),
    path('file-versions/<str:file_id>/',              FileVersionsView.as_view(),            name='file-versions'),

    # ── File Docs (للاستخدام في كشف التناقض code-doc) ───────────────────────
    path('file-docs/<str:file_id>/',                  FileDocsView.as_view(),                name='file-docs'),
]