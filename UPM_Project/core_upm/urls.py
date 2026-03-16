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
]