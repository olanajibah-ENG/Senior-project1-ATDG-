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
]