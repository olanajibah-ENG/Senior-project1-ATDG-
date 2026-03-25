from django.urls import path , include
from rest_framework.routers import DefaultRouter
from core_upm.views import (
    UserRegistrationAPIView,
    UserLoginAPIView,
    ProjectListCreateAPIView,
    ProjectRetrieveUpdateDestroyAPIView,
    ArtifactListCreateAPIView,
    ArtifactRetrieveUpdateDestroyAPIView
)
from core_upm.views.folder_views import (
    FolderListCreateAPIView,
    FolderRetrieveUpdateDestroyAPIView
)
from core_upm.views.folder_upload_proxy import FolderUploadProxyView
<<<<<<< HEAD
=======
from core_upm.views.github_views import (
    GitHubConnectView,
    GitHubSyncView,
    GitHubWebhookView
)
>>>>>>> feature/github-integration

urlpatterns = [
    # User authentication
    path('signup/', UserRegistrationAPIView.as_view(), name='register'),
    path('login/', UserLoginAPIView.as_view(), name='login'),

    # Projects
    path('projects/', ProjectListCreateAPIView.as_view(), name='project-list-create'),
    path('projects/<uuid:project_id>/', ProjectRetrieveUpdateDestroyAPIView.as_view(), name='project-detail'),

    # Artifacts
    path('projects/<uuid:project_id>/artifacts/', ArtifactListCreateAPIView.as_view(), name='artifact-list-create'),
    path('artifacts/<uuid:code_id>/', ArtifactRetrieveUpdateDestroyAPIView.as_view(), name='artifact-detail'),

    # Folders — CRUD
    path('projects/<uuid:project_id>/folders/', FolderListCreateAPIView.as_view(), name='folder-list-create'),
    path('folders/<uuid:folder_id>/', FolderRetrieveUpdateDestroyAPIView.as_view(), name='folder-detail'),

    # Folder Upload — مرتبط بالمشروع تلقائياً من الـ URL
    path('projects/<uuid:project_id>/folder-upload/', FolderUploadProxyView.as_view(), name='folder-upload'),
<<<<<<< HEAD
=======

    # GitHub Integration
    path('projects/<uuid:project_id>/github/connect/', GitHubConnectView.as_view(), name='github-connect'),
    path('projects/<uuid:project_id>/github/sync/', GitHubSyncView.as_view(), name='github-sync'),
    path('projects/<uuid:project_id>/github/webhook/', GitHubWebhookView.as_view(), name='github-webhook'),
>>>>>>> feature/github-integration
]