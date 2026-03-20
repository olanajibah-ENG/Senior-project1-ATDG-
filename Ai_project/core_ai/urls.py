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
    throughput_24h_view,
    avg_queue_time_view,
    duration_by_lang_view,
    agent_breakdown_view,
    explanation_quality_view,
    error_classification_view,
    size_distribution_view,
    generated_files_stats_view,
    celery_health_view
)
from core_ai.views.evaluation_views import (
    evaluate_explanation,
    get_evaluation_history,
    get_evaluation_stats,
    submit_human_review
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
    
    path('reviewer/stats/', reviewer_stats_view, name='reviewer-stats'),
    path('reviewer/stats/throughput-24h/', throughput_24h_view, name='throughput-24h'),
    path('reviewer/stats/avg-queue-time/', avg_queue_time_view, name='avg-queue-time'),
    path('reviewer/stats/duration-by-lang/', duration_by_lang_view, name='duration-by-lang'),
    path('reviewer/stats/agent-breakdown/', agent_breakdown_view, name='agent-breakdown'),
    path('reviewer/stats/explanation-quality/', explanation_quality_view, name='explanation-quality'),
    path('reviewer/stats/error-classification/', error_classification_view, name='error-classification'),
    path('reviewer/stats/size-distribution/', size_distribution_view, name='size-distribution'),
    path('reviewer/stats/generated-files/', generated_files_stats_view, name='generated-files-stats'),
    path('reviewer/stats/celery-health/', celery_health_view, name='celery-health'),
    
    # Evaluation endpoints
    path('evaluate-explanation/<str:explanation_id>/', evaluate_explanation, name='evaluate-explanation'),
    path('evaluation-history/<str:explanation_id>/', get_evaluation_history, name='evaluation-history'),
    path('evaluation-stats/', get_evaluation_stats, name='evaluation-stats'),
    path('submit-human-review/<str:explanation_id>/', submit_human_review, name='submit-human-review'),
]
