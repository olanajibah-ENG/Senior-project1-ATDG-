from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import requests
from rest_framework import viewsets, status # Make sure to import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core_upm.business_logic import ProjectService
from core_upm.models.project import Project
from core_upm.serializers.project_serializer import ProjectListCreateSerializer
from core_upm.serializers.project_serializer import ProjectRetrieveUpdateDestroySerializer
from core_upm.notification_utils import NotificationClient

class ProjectPagination(PageNumberPagination):
    """Pagination class for Project list views."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@method_decorator(csrf_exempt, name='dispatch')
class ProjectListCreateAPIView(ListCreateAPIView):
    """
    List all projects or create a new project.
    """
    # Define permissions: requires authenticated user
    permission_classes = [IsAuthenticated]

    # Define pagination class
    pagination_class = ProjectPagination

    def get_queryset(self):
        """
        Admins see all projects; other users see only their own.
        """
        user = self.request.user
        try:
            is_admin = user.profile.role_type == 'ADMIN'
        except Exception:
            is_admin = False

        if is_admin:
            return Project.objects.all().order_by('-creation_date')

        service = ProjectService()
        return service.get_user_projects(user=user)

    def get_serializer_class(self):
        # Local import of Serializer to avoid circular dependency
        from core_upm.serializers.project_serializer import ProjectListCreateSerializer
        return ProjectListCreateSerializer

    def perform_create(self, serializer):
        """
        Override create operation to use Business Service.
        """
        service = ProjectService()
        # Map serializer validated_data (title/description) to service expected format (project_name/project_description)
        service_data = {
            'project_name': serializer.validated_data.get('project_name'),
            'project_description': serializer.validated_data.get('project_description', '')
        }
        project = service.create_new_project(user=self.request.user, data=service_data)
        # Update serializer instance with created project
        serializer.instance = project

        # Send project creation success notification
        try:
            NotificationClient.send_project_notification(
                user_email=self.request.user.email,
                action='created',
                project_name=project.project_name,
                project_id=str(project.project_id),
                user_name=self.request.user.username
            )
        except Exception as e:
            # We don't want notification failure to affect the success of the main operation
            pass


@method_decorator(csrf_exempt, name='dispatch')
class ProjectRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific project.
    """
    # Define permissions
    permission_classes = [IsAuthenticated]

    # Define lookup field in URL
    lookup_field = 'project_id'
    lookup_url_kwarg = 'project_id'

    def get_queryset(self):
        """
        Filter projects to show only the current user's projects.
        Filter projects to show only the current user's projects.
        """
        service = ProjectService()
        return service.get_user_projects(user=self.request.user) 

    def get_serializer_class(self):
        # Local import of Serializer to avoid circular dependency
        from core_upm.serializers.project_serializer import ProjectRetrieveUpdateDestroySerializer 
        return ProjectRetrieveUpdateDestroySerializer

    def perform_update(self, serializer):
        """
        Override update operation to use Business Service.
        """
        service = ProjectService()
        project = self.get_object()
        # Map serializer validated_data (title/description) to service expected format (project_name/project_description)
        service_data = {}
        if 'project_name' in serializer.validated_data:
            service_data['project_name'] = serializer.validated_data['project_name']
        if 'project_description' in serializer.validated_data:
            service_data['project_description'] = serializer.validated_data['project_description']
        updated_project = service.update_project(
            project=project,
            data=service_data,
            user=self.request.user
        )
        # Update serializer instance with updated project
        serializer.instance = updated_project
        
    def perform_destroy(self, instance):
        """
        Override delete operation to use Business Service.
        """
        # Save project information before deletion for notification
        project_name = instance.project_name
        project_id = str(instance.project_id)

        service = ProjectService()
        service.delete_project(project_id=project_id, user=self.request.user)

        # Send project deletion notification
        try:
            NotificationClient.send_project_notification(
                user_email=self.request.user.email,
                action='deleted',
                project_name=project_name,
                project_id=project_id,
                user_name=self.request.user.username
            )
        except Exception as e:
            # We don't want notification failure to affect the success of the main operation
            pass


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all() # Re-enable these lines if disabled
      # <<< Use get_serializer_class to determine serializer based on action >>>
    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return ProjectListCreateSerializer
        # For 'retrieve', 'update', 'partial_update', 'destroy' and custom action 'send_for_analysis'
        return ProjectRetrieveUpdateDestroySerializer

    # ... existing code for other actions (list, retrieve, create, update, delete) ...

    @action(detail=True, methods=['post'])
    def send_for_analysis(self, request, pk=None):
        project = self.get_object() # Get project object from URL
        
        mock_code_content = f"print('Hello from UPM Project {project.project_name}, ID: {project.project_id}\\nThis is some mock Python code for analysis.')"
        mock_filename = f"project_{project.project_id}_main.py"
        mock_file_type = "python" # Should be extracted dynamically based on file type

        # URL for internal Ai_project service (service name in docker-compose: ai_web)
        ai_service_url = "http://ai_web:8000/api/analysis/codefiles/"

        try:
            response = requests.post(
                ai_service_url,
                json={
                    "filename": mock_filename,
                    "file_type": mock_file_type,
                    "content": mock_code_content,
                    "source_project_id": str(project.project_id) # To link analysis to original project
                }
            )
            response.raise_for_status() # Raises exception for any HTTP error (4xx or 5xx)
            ai_response_data = response.json()
            
            # Here you can store ai_response_data.get('id') (which is CodeFile ID in Ai_project)
            # or ai_response_data.get('job_id') if Ai_project response starts analysis directly
            # to maintain reference in UPM_Project
            # project.analysis_code_file_id = ai_response_data.get('id')
            # project.save()

            return Response(
                {"message": "Code sent for analysis", "ai_response": ai_response_data},
                status=status.HTTP_202_ACCEPTED
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Failed to send code for analysis: {e}. AI Service might be down or misconfigured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )