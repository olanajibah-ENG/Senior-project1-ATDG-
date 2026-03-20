import logging
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db.models import Count, Q, F
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core_upm.models.project import Project
from core_upm.permissions import IsAdminRole
from core_upm.serializers.project_serializer import ProjectListCreateSerializer
from core_upm.serializers.user_serializer import UserDetailSerializer

logger = logging.getLogger(__name__)


class AdminStatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            now = timezone.now()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            cutoff_online = now - timedelta(minutes=5)

            total_users = User.objects.count()

            users_by_role = User.objects.values('profile__role__role_type').annotate(
                count=Count('id')
            ).filter(profile__role__role_type__isnull=False)
            users_by_role_dict = {item['profile__role__role_type']: item['count'] for item in users_by_role}

            new_users_this_week = User.objects.filter(
                date_joined__gte=week_ago
            ).count()

            total_projects = Project.objects.count()

            projects_this_month = Project.objects.filter(
                creation_date__gte=month_ago
            ).count()

            most_active_developers = User.objects.filter(
                projects__isnull=False,
                profile__role__role_type='DEVELOPER'
            ).annotate(
                project_count=Count('projects')
            ).order_by('-project_count')[:10].values(
                'username', 'email', 'project_count'
            )

            inactive_threshold = now - timedelta(days=30)
            inactive_users = User.objects.filter(
                Q(profile__last_seen__lt=inactive_threshold) | 
                Q(profile__last_seen__isnull=True)
            ).count()

            online_now = User.objects.filter(
                profile__last_seen__gte=cutoff_online
            ).count()

            stats = {
                'total_users': total_users,
                'users_by_role': users_by_role_dict,
                'new_users_this_week': new_users_this_week,
                'total_projects': total_projects,
                'projects_this_month': projects_this_month,
                'most_active_developers': list(most_active_developers),
                'inactive_users': inactive_users,
                'online_now': online_now,
            }

            logger.info("AdminStatsView: Stats computed successfully")
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"AdminStatsView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminProjectsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            queryset = Project.objects.select_related('user').all()

            filter_by_user = request.query_params.get('user_id')
            if filter_by_user:
                queryset = queryset.filter(user_id=filter_by_user)

            search_query = request.query_params.get('search')
            if search_query:
                queryset = queryset.filter(project_name__icontains=search_query)

            sort_by = request.query_params.get('sort_by', '-creation_date')
            queryset = queryset.order_by(sort_by)

            serializer = ProjectListCreateSerializer(queryset, many=True)
            logger.info(f"AdminProjectsView: {queryset.count()} projects retrieved")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"AdminProjectsView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AccountMeView(APIView):
    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return Response(
                    {'detail': 'Not authenticated'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            serializer = UserDetailSerializer(request.user)
            logger.info(f"AccountMeView: User {request.user.username} info retrieved")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"AccountMeView error: {str(e)}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
