from django.urls import path , include
from rest_framework.routers import DefaultRouter
from core_upm.views import (
    UserRegistrationAPIView,
    UserLoginAPIView,
    ProjectListCreateAPIView,
    ProjectRetrieveUpdateDestroyAPIView,
    ArtifactListCreateAPIView,
    ArtifactRetrieveUpdateDestroyAPIView,
    AdminUserListView,
    AdminCreateReviewerView,
    AdminToggleUserActiveView,
    ChangePasswordView,
    OnlineUsersView,
    ReviewerNotifyAdminView,
)

from core_upm.views.github_views import (
    GitHubConnectView,
    GitHubSyncView,
    GitHubWebhookView
)


from core_upm.views.folder_views import (
    FolderListCreateAPIView,
    FolderRetrieveUpdateDestroyAPIView
)
from core_upm.views.folder_upload_proxy import FolderUploadProxyView


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

    # Admin / account endpoints
    path('admin/users/',
         AdminUserListView.as_view(),
         name='admin-user-list'),

    path('admin/users/create-reviewer/',
         AdminCreateReviewerView.as_view(),
         name='admin-create-reviewer'),

    path('admin/users/<int:user_id>/toggle-active/',
         AdminToggleUserActiveView.as_view(),
         name='admin-toggle-active'),

    path('account/change-password/',
         ChangePasswordView.as_view(),
         name='change-password'),

    path('users/online/',
         OnlineUsersView.as_view(),
         name='online-users'),

    path('reviewer/notify-admin/',
         ReviewerNotifyAdminView.as_view(),
         name='reviewer-notify-admin'),
    path('projects/<uuid:project_id>/github/connect/', GitHubConnectView.as_view(), name='github-connect'),
    path('projects/<uuid:project_id>/github/sync/', GitHubSyncView.as_view(), name='github-sync'),
    path('projects/<uuid:project_id>/github/webhook/', GitHubWebhookView.as_view(), name='github-webhook'),     
    path('projects/<uuid:project_id>/folders/', FolderListCreateAPIView.as_view(), name='folder-list-create'),
    path('folders/<uuid:folder_id>/', FolderRetrieveUpdateDestroyAPIView.as_view(), name='folder-detail'),

    # Folder Upload — مرتبط بالمشروع تلقائياً من الـ URL
    path('projects/<uuid:project_id>/folder-upload/', FolderUploadProxyView.as_view(), name='folder-upload'),
]