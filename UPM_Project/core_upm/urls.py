from django.urls import path
from core_upm.views import (
    UserRegistrationAPIView,
    UserLoginAPIView,
    ProjectListCreateAPIView,
    ProjectRetrieveUpdateDestroyAPIView,
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
    GitHubWebhookView,
)
from core_upm.views.folder_views import (
    FolderListCreateAPIView,
    FolderRetrieveUpdateDestroyAPIView,
)
from core_upm.views.folder_upload_proxy import FolderUploadProxyView
from core_upm.views.project_tree_proxy import (
    ProjectVersionsProxyView,
    ProjectTreeProxyView,
    FileContentProxyView,
)

urlpatterns = [

    # ── Auth ──────────────────────────────────────────────────────────────────
    path('signup/', UserRegistrationAPIView.as_view(), name='register'),
    path('login/',  UserLoginAPIView.as_view(),        name='login'),

    # ── Projects ──────────────────────────────────────────────────────────────
    path('projects/',
         ProjectListCreateAPIView.as_view(),
         name='project-list-create'),
    path('projects/<uuid:project_id>/',
         ProjectRetrieveUpdateDestroyAPIView.as_view(),
         name='project-detail'),

    # ── رفع الملفات (ملف واحد / ملفات متعددة / ZIP / مجلد كامل) ─────────────
    path('projects/<uuid:project_id>/folder-upload/',
         FolderUploadProxyView.as_view(),
         name='folder-upload'),

    # ── الإصدارات والشجرة ─────────────────────────────────────────────────────
    # الخطوة 1: جيب كل الإصدارات المتاحة (dropdown للمستخدم)
    path('projects/<uuid:project_id>/versions/',
         ProjectVersionsProxyView.as_view(),
         name='project-versions'),
    # الخطوة 2: جيب شجرة إصدار محدد — ?version=N أو بدونه لآخر إصدار
    path('projects/<uuid:project_id>/tree/',
         ProjectTreeProxyView.as_view(),
         name='project-tree'),
    # الخطوة 3: جيب محتوى ملف واحد (لما المستخدم يكبس على ملف في الشجرة)
    path('projects/<uuid:project_id>/files/<str:file_id>/content/',
         FileContentProxyView.as_view(),
         name='file-content'),

    # ── Folders ───────────────────────────────────────────────────────────────
    path('projects/<uuid:project_id>/folders/',
         FolderListCreateAPIView.as_view(),
         name='folder-list-create'),
    path('folders/<uuid:folder_id>/',
         FolderRetrieveUpdateDestroyAPIView.as_view(),
         name='folder-detail'),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path('admin/users/',
         AdminUserListView.as_view(),
         name='admin-user-list'),
    path('admin/users/create-reviewer/',
         AdminCreateReviewerView.as_view(),
         name='admin-create-reviewer'),
    path('admin/users/<int:user_id>/toggle-active/',
         AdminToggleUserActiveView.as_view(),
         name='admin-toggle-active'),

    # ── Account ───────────────────────────────────────────────────────────────
    path('account/change-password/',
         ChangePasswordView.as_view(),
         name='change-password'),
    path('users/online/',
         OnlineUsersView.as_view(),
         name='online-users'),

    # ── Reviewer ──────────────────────────────────────────────────────────────
    path('reviewer/notify-admin/',
         ReviewerNotifyAdminView.as_view(),
         name='reviewer-notify-admin'),

    # ── GitHub ────────────────────────────────────────────────────────────────
    path('projects/<uuid:project_id>/github/connect/',
         GitHubConnectView.as_view(),
         name='github-connect'),
    path('projects/<uuid:project_id>/github/sync/',
         GitHubSyncView.as_view(),
         name='github-sync'),
    path('projects/<uuid:project_id>/github/webhook/',
         GitHubWebhookView.as_view(),
         name='github-webhook'),
]