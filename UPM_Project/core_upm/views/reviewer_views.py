import logging
import requests
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

from core_upm.models.project import Project
from core_upm.models.user import UserProfile
from core_upm.serializers.project_serializer import ProjectListCreateSerializer
from core_upm.permissions import IsAdminOrReviewer, IsReviewerRole

logger = logging.getLogger(__name__)


class BaseAIProxyView(APIView):
    permission_classes = [IsAdminOrReviewer]

    def call_ai(self, path, params=None):
        try:
            ai_url = settings.AI_SERVICE_URL.rstrip('/') + '/' + path.lstrip('/')
            headers = {
                'Authorization': f'Bearer {settings.AI_SERVICE_KEY}',
                'Content-Type': 'application/json',
            }
            
            response = requests.get(ai_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"AI Service call successful: {path}")
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"AI Service timeout: {path}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"AI Service connection error: {path}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"AI Service HTTP error {response.status_code}: {path}")
            return None
        except Exception as e:
            logger.error(f"AI Service error: {str(e)}")
            return None


class ReviewerStatsView(BaseAIProxyView):
    def get(self, request):
        try:
            result = self.call_ai('stats/')
            if result is None:
                return Response(
                    {'detail': 'Failed to fetch stats from AI service'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            logger.info("ReviewerStatsView: Stats retrieved successfully")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ReviewerStatsView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewerAnalysisResultsView(BaseAIProxyView):
    def get(self, request):
        try:
            params = {
                'limit': request.query_params.get('limit', 50),
                'offset': request.query_params.get('offset', 0),
            }
            result = self.call_ai('analysis-results/', params=params)
            if result is None:
                return Response(
                    {'detail': 'Failed to fetch analysis results'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            logger.info("ReviewerAnalysisResultsView: Results retrieved successfully")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ReviewerAnalysisResultsView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewerAnalysisDetailView(BaseAIProxyView):
    def get(self, request, analysis_id):
        try:
            result = self.call_ai(f'analysis-results/{analysis_id}/')
            if result is None:
                return Response(
                    {'detail': 'Analysis not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            logger.info(f"ReviewerAnalysisDetailView: Analysis {analysis_id} retrieved")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ReviewerAnalysisDetailView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewerJobsView(BaseAIProxyView):
    def get(self, request):
        try:
            params = {
                'limit': request.query_params.get('limit', 50),
                'offset': request.query_params.get('offset', 0),
                'status': request.query_params.get('status'),
            }
            params = {k: v for k, v in params.items() if v is not None}
            result = self.call_ai('jobs/', params=params)
            if result is None:
                return Response(
                    {'detail': 'Failed to fetch jobs'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            logger.info("ReviewerJobsView: Jobs retrieved successfully")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ReviewerJobsView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewerAITasksView(BaseAIProxyView):
    def get(self, request):
        try:
            params = {
                'limit': request.query_params.get('limit', 50),
                'offset': request.query_params.get('offset', 0),
            }
            result = self.call_ai('ai-tasks/', params=params)
            if result is None:
                return Response(
                    {'detail': 'Failed to fetch AI tasks'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            logger.info("ReviewerAITasksView: AI tasks retrieved successfully")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ReviewerAITasksView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewerExplanationsView(BaseAIProxyView):
    def get(self, request):
        try:
            params = {
                'limit': request.query_params.get('limit', 50),
                'offset': request.query_params.get('offset', 0),
            }
            result = self.call_ai('explanations/', params=params)
            if result is None:
                return Response(
                    {'detail': 'Failed to fetch explanations'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            logger.info("ReviewerExplanationsView: Explanations retrieved successfully")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ReviewerExplanationsView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewerGeneratedFilesView(BaseAIProxyView):
    def get(self, request):
        try:
            params = {
                'limit': request.query_params.get('limit', 50),
                'offset': request.query_params.get('offset', 0),
            }
            result = self.call_ai('generated-files/', params=params)
            if result is None:
                return Response(
                    {'detail': 'Failed to fetch generated files'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            logger.info("ReviewerGeneratedFilesView: Generated files retrieved successfully")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ReviewerGeneratedFilesView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewerProjectsView(APIView):
    permission_classes = [IsAdminOrReviewer]

    def get(self, request):
        try:
            queryset = Project.objects.select_related('user').all()
            
            filter_by_user = request.query_params.get('user_id')
            if filter_by_user:
                queryset = queryset.filter(user_id=filter_by_user)
            
            search_query = request.query_params.get('search')
            if search_query:
                queryset = queryset.filter(project_name__icontains=search_query)
            
            serializer = ProjectListCreateSerializer(queryset, many=True)
            logger.info(f"ReviewerProjectsView: {queryset.count()} projects retrieved")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ReviewerProjectsView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewerNotifyAdminView(APIView):
    permission_classes = [IsReviewerRole]

    def post(self, request):
        try:
            title = request.data.get('title')
            message = request.data.get('message')
            related_id = request.data.get('related_id')
            related_type = request.data.get('related_type')

            if not all([title, message, related_id, related_type]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            admin_user = User.objects.filter(
                profile__role__role_type='ADMIN'
            ).first()

            if not admin_user:
                return Response(
                    {'error': 'Admin user not found'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            notification_url = getattr(settings, 'NOTIFICATION_SERVICE_URL', 'http://notification_django:8000') + '/api/notify/reviewer-alert/'
            
            payload = {
                'admin_email': admin_user.email,
                'reviewer_name': request.user.profile.full_name,
                'title': title,
                'message': message,
                'related_id': related_id,
                'related_type': related_type
            }

            response = requests.post(
                notification_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            logger.info(f"Reviewer {request.user.profile.full_name} sent notification to admin {admin_user.email}")
            return Response(
                {'status': 'success', 'message': 'Notification sent to admin'},
                status=status.HTTP_200_OK
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send notification to admin: {str(e)}")
            return Response(
                {'error': 'Failed to send notification'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"ReviewerNotifyAdminView error: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

