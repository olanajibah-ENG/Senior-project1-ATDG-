import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from core_ai.services.reviewer_stats_service import ReviewerStatsService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def reviewer_stats_view(request):
    """GET /reviewer/stats/ — returns all stats in one call"""
    try:
        service = ReviewerStatsService()
        stats = service.get_all_stats()
        if stats is None:
            return Response({"detail": "Failed to retrieve statistics"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in reviewer_stats_view: {str(e)}")
        return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def ai_tasks_list_view(request):
    """
    GET /reviewer/ai-tasks/
    ?status=completed|failed|processing|pending
    ?exp_type=high_level|low_level
    ?limit=100 (max 500)
    """
    try:
        from django.conf import settings
        from core_ai.mongo_utils import get_mongo_db

        db = get_mongo_db()
        if db is None:
            return Response({"detail": "Database unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        collection = db[settings.AI_TASKS_COLLECTION]

        query = {}
        status_filter = request.GET.get('status')
        exp_type_filter = request.GET.get('exp_type')
        if status_filter:
            query['status'] = status_filter
        if exp_type_filter:
            query['exp_type'] = exp_type_filter

        limit = min(int(request.GET.get('limit', 100)), 500)
        tasks = list(collection.find(query).sort('created_at', -1).limit(limit))

        for t in tasks:
            t['_id'] = str(t['_id'])
            if 'analysis_id' in t:
                t['analysis_id'] = str(t['analysis_id'])

        return Response({
            "count": len(tasks),
            "filters": {"status": status_filter, "exp_type": exp_type_filter},
            "tasks": tasks
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in ai_tasks_list_view: {str(e)}")
        return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
