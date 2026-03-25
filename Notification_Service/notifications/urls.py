from django.urls import path
from . import views

# URLs الخاصة بالتطبيق - مع دعم Celery Async Processing
urlpatterns = [
    # Routes لإنشاء أنواع الإشعارات المحددة (الآن تستخدم Celery)
    path('api/notifications/project/', views.create_project_notification, name='project-notification'),
    path('api/notifications/code/', views.create_code_notification, name='code-notification'),
    path('api/notifications/documentation/', views.create_documentation_notification, name='documentation-notification'),
    path('api/notifications/user/', views.create_user_notification, name='user-notification'),
    path('api/notifications/system/', views.create_system_alert, name='system-alert'),
    path('api/notifications/custom/', views.create_custom_notification, name='custom-notification'),
    path('api/notifications/create/', views.create_custom_notification, name='create-notification'),  # ✅ Alias
    path('api/notify/reviewer-alert/', views.create_reviewer_alert, name='reviewer-alert'),
    path('api/notifications/settings/', views.notification_settings, name='notification-settings'),
    
    # ✅ Endpoint جديد للتحقق من حالة Celery Task
    path('api/notifications/task-status/', views.get_notification_task_status, name='notification-task-status'),
    
    # Routes جديدة للحصول على الإشعارات وإدارتها
    path('api/notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('api/notifications/stats/', views.NotificationStatsView.as_view(), name='notification-stats'),
    path('api/notifications/mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('api/notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('api/notifications/<int:notification_id>/mark-read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('api/notifications/<int:notification_id>/resend/', views.NotificationResendView.as_view(), name='notification-resend'),
    path('api/notifications/<int:notification_id>/delete/', views.NotificationDeleteView.as_view(), name='notification-delete'),
]
