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
    """
    Get comprehensive reviewer statistics
    Returns: all_stats including performance, quality, files, and celery metrics
    """
    try:
        service = ReviewerStatsService()
        stats = service.get_all_stats()
        
        if stats is None:
            logger.error("Failed to retrieve stats")
            return Response(
                {"detail": "Failed to retrieve statistics"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        logger.info("Reviewer stats retrieved successfully")
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in reviewer_stats_view: {str(e)}")
        return Response(
            {"detail": "Internal server error", "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def throughput_24h_view(request):
    """
    Get throughput for last 24 hours
    """
    try:
        service = ReviewerStatsService()
        result = service.get_throughput_24h()
        
        if result is None:
            return Response(
                {"detail": "Failed to retrieve throughput data"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in throughput_24h_view: {str(e)}")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def avg_queue_time_view(request):
    """
    Get average queue time
    """
    try:
        service = ReviewerStatsService()
        result = service.get_avg_queue_time()
        
        if result is None:
            return Response(
                {"detail": "Failed to retrieve queue time data"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in avg_queue_time_view: {str(e)}")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def duration_by_lang_view(request):
    """
    Get average duration by programming language
    """
    try:
        service = ReviewerStatsService()
        result = service.get_avg_duration_by_lang()
        
        if result is None:
            return Response(
                {"detail": "Failed to retrieve duration data"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in duration_by_lang_view: {str(e)}")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def agent_breakdown_view(request):
    """
    Get agent task breakdown with error rates
    """
    try:
        service = ReviewerStatsService()
        result = service.get_agent_breakdown()
        
        if result is None:
            return Response(
                {"detail": "Failed to retrieve agent breakdown"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in agent_breakdown_view: {str(e)}")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def explanation_quality_view(request):
    """
    Get explanation quality metrics
    """
    try:
        service = ReviewerStatsService()
        result = service.get_explanation_quality()
        
        if result is None:
            return Response(
                {"detail": "Failed to retrieve explanation data"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in explanation_quality_view: {str(e)}")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def error_classification_view(request):
    """
    Get error classification and breakdown
    """
    try:
        service = ReviewerStatsService()
        result = service.get_error_classification()
        
        if result is None:
            return Response(
                {"detail": "Failed to retrieve error data"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in error_classification_view: {str(e)}")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def size_distribution_view(request):
    """
    Get code file size distribution
    """
    try:
        service = ReviewerStatsService()
        result = service.get_size_distribution()
        
        if result is None:
            return Response(
                {"detail": "Failed to retrieve size distribution"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in size_distribution_view: {str(e)}")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def generated_files_stats_view(request):
    """
    Get generated files statistics
    """
    try:
        service = ReviewerStatsService()
        result = service.get_generated_files_stats()
        
        if result is None:
            return Response(
                {"detail": "Failed to retrieve generated files data"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in generated_files_stats_view: {str(e)}")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def celery_health_view(request):
    """
    Get Celery health status
    """
    try:
        service = ReviewerStatsService()
        result = service.get_celery_health()
        
        if result is None:
            return Response(
                {"detail": "Failed to retrieve Celery status"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in celery_health_view: {str(e)}")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
