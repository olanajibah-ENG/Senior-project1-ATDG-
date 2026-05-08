import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .models import Notification
from .tasks import (
    send_project_notification_task,
    send_code_notification_task,
    send_documentation_notification_task,
    send_custom_notification_task
)
from . import notification_service
from .serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationListSerializer,
    NotificationUpdateSerializer,
    NotificationSettingsSerializer,
)
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([AllowAny])
def create_project_notification(request):
    try:
        data = request.data
        user_email = data.get('user_email')
        action = data.get('action')
        project_name = data.get('project_name')

        # 1. إنشاء السجل بحالة PROCESSING
        notification = Notification.objects.create(
            user_email=user_email,
            user_name=data.get('user_name', ''),
            notification_type='PROJECT_CREATED' if action == 'created' else 'PROJECT_DELETED',
            title=f"Project {action}",
            message=f"Project '{project_name}' has been {action}",
            status='PROCESSING'
        )

        # 2. تمرير الـ notification_id للتاسك ليعرف أي سجل يحدث
        task = send_project_notification_task.delay(
            notification_id=notification.id,
            **data
        )

        notification.task_id = task.id
        notification.save()
        
        return Response({
            'notification_id': notification.id, 
            'task_id': task.id,
            'status': notification.status,
            'message': notification.message,
            'type': notification.notification_type
        }, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_code_notification(request):
    try:
        data = request.data
        notification = Notification.objects.create(
            user_email=data.get('user_email'),
            user_name=data.get('user_name', ''),
            notification_type='CODE_ADDED' if data.get('action') == 'added' else 'CODE_DELETED',
            title=f"Code {data.get('action')}",
            message=f"Code '{data.get('code_name')}' has been {data.get('action')}",
            status='PROCESSING'
        )
        task = send_code_notification_task.delay(notification_id=notification.id, **data)
        notification.task_id = task.id
        notification.save()
        return Response({
            'notification_id': notification.id,
            'task_id': task.id,
            'status': notification.status,
            'message': notification.message,
            'type': notification.notification_type
        }, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_documentation_notification(request):
    try:
        notification = Notification.objects.create(
            user_email=request.data.get('user_email'),
            user_name=request.data.get('user_name', ''),
            notification_type='DOCUMENTATION_EXPORTED',
            title="Documentation Exported",
            message=f"Documentation '{request.data.get('file_name')}' has been exported successfully",
            status='PROCESSING'
        )
        task = send_documentation_notification_task.delay(notification_id=notification.id, **request.data)
        notification.task_id = task.id
        notification.save()
        return Response({
            'notification_id': notification.id,
            'task_id': task.id,
            'status': notification.status,
            'message': notification.message,
            'type': notification.notification_type
        }, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_custom_notification(request):
    try:
        notification = Notification.objects.create(
            user_email=request.data.get('user_email'),
            user_name=request.data.get('user_name', ''),
            notification_type=request.data.get('notification_type', 'CUSTOM'),
            title=request.data.get('title'),
            message=request.data.get('message', ''),
            status='PROCESSING'
        )
        task = send_custom_notification_task.delay(
            notification_id=notification.id,
            user_email=request.data.get('user_email'),
            title=request.data.get('title'),
            message=request.data.get('message'),
            notification_type=request.data.get('notification_type', 'CUSTOM')
        )
        notification.task_id = task.id
        notification.save()
        return Response({
            'notification_id': notification.id,
            'task_id': task.id,
            'status': notification.status,
            'message': notification.message,
            'type': notification.notification_type
        }, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_user_notification(request):
    """Create a user-related notification (register/password change/etc.)"""
    try:
        data = request.data
        user_email = data.get('user_email')
        action = data.get('action')
        user_name = data.get('user_name', '')

        # Create DB record
        notification = Notification.objects.create(
            user_email=user_email,
            user_name=user_name,
            notification_type='USER_REGISTERED' if action == 'registered' else 'PASSWORD_CHANGED' if action == 'password_changed' else 'USER_ACTION',
            title=f"User {action}",
            message=f"User action: {action}",
            status='PROCESSING'
        )

        # Send synchronously via helper (SimpleNotification)
        notification_obj = notification_service.send_user_notification(user_email=user_email, action=action, user_name=user_name)
        notification.status = 'SENT'
        notification.message = f"User {action} notification sent successfully"
        notification.save()
        return Response({
            'notification_id': notification.id, 
            'status': notification.status,
            'message': notification.message,
            'type': notification.notification_type
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_system_alert(request):
    try:
        data = request.data
        user_email = data.get('user_email', '')
        user_name = data.get('user_name', '')
        title = data.get('title', 'System Alert')
        message_text = data.get('message', '')
        priority = data.get('priority', 'MEDIUM')
        alert_type = data.get('type', 'GENERAL')

        # Create notification record in database
        notification = Notification.objects.create(
            user_email=user_email,
            user_name=user_name,
            notification_type='SYSTEM_ALERT',
            title=title,
            message=message_text,
            priority=priority,
            status='SENT'
        )

        # Send the alert
        notification_obj = notification_service.send_system_alert(
            user_email=user_email, 
            alert_type=alert_type, 
            message=message_text
        )
        
        return Response({
            'notification_id': notification.id,
            'status': notification.status,
            'priority': notification.priority,
            'message': title
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_reviewer_alert(request):
    try:
        data = request.data
        admin_email = data.get('admin_email')
        reviewer_name = data.get('reviewer_name')
        title = data.get('title')
        message = data.get('message')
        related_id = data.get('related_id')
        related_type = data.get('related_type')

        if not all([admin_email, reviewer_name, title, message]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        notification = Notification.objects.create(
            user_email=admin_email,
            user_name='Admin',
            notification_type='REVIEWER_ALERT',
            title=title,
            message=message,
            related_id=related_id,
            related_type=related_type,
            status='PROCESSING'
        )

        notification_obj = notification_service.SimpleNotification(
            user_email=admin_email,
            notification_type='REVIEWER_ALERT',
            title=title,
            message=message,
            user_name='Admin',
            related_id=related_id,
            related_type=related_type
        )

        if notification_obj.send_email():
            notification.status = 'SENT'
            notification.save()
            return Response({'status': 'sent'}, status=status.HTTP_200_OK)
        else:
            notification.status = 'SAVED'
            notification.save()
            # Email delivery failed but notification is saved — not a hard error
            return Response({'status': 'saved', 'message': 'Notification saved, email delivery unavailable'}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_notification_task_status(request):
    task_id = request.query_params.get('task_id')
    if not task_id:
        return Response({'error': 'task_id required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        obj = Notification.objects.filter(task_id=task_id).first()
        if not obj:
            return Response({'status': 'unknown'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'status': obj.status, 'error_message': obj.error_message}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def notification_settings(request):
    # Return default settings for the service (could be extended)
    serializer = NotificationSettingsSerializer({
        'email_enabled': True,
        'notification_types_enabled': {
            'PROJECT_CREATED': True,
            'CODE_ADDED': True,
            'DOCUMENTATION_EXPORTED': True,
            'SYSTEM_ALERT': True,
        },
        'email_frequency': 'immediate',
        'storage_type': 'database'
    })
    return Response(serializer.data)


class NotificationListView(generics.ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationListSerializer
    permission_classes = [AllowAny]
    
    # Setup logger
    logger = logging.getLogger(__name__)
    
    def get_queryset(self):
        """
        Get notifications filtered by user_email from query params
        Returns empty list if no notifications found instead of 500 error
        """
        try:
            # Start with base queryset ordered by creation date
            queryset = Notification.objects.all().order_by('-created_at')
            
            # Get user_email from query params
            user_email = self.request.query_params.get('user_email')
            
            if user_email:
                # Log the filtering attempt
                self.logger.info(f"Filtering notifications for user_email: {user_email}")
                
                # Filter by user_email - use filter() instead of get() to avoid exceptions
                queryset = queryset.filter(user_email=user_email)
                
                # Log the count for debugging
                count = queryset.count()
                self.logger.info(f"Found {count} notifications for user_email: {user_email}")
            else:
                self.logger.warning("No user_email parameter provided in request")
            
            return queryset
            
        except Exception as e:
            # Log the full error with traceback
            self.logger.error(f"Error in get_queryset for user_email {user_email}: {str(e)}", exc_info=True)
            
            # Return empty queryset instead of raising exception
            return Notification.objects.none()
    
    def list(self, request, *args, **kwargs):
        """
        Override list method to add additional error handling
        """
        try:
            # Call parent list method
            response = super().list(request, *args, **kwargs)
            
            # Log successful response
            user_email = request.query_params.get('user_email', 'unknown')
            self.logger.info(f"Successfully returned {len(response.data)} notifications for user: {user_email}")
            
            return response
            
        except Exception as e:
            # Log the error
            user_email = request.query_params.get('user_email', 'unknown')
            self.logger.error(f"Error in list method for user {user_email}: {str(e)}", exc_info=True)
            
            # Return empty list with 200 status instead of 500
            return Response([], status=status.HTTP_200_OK)


class NotificationDetailView(generics.RetrieveAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'
    
    def get_exception_handler_context(self):
        """Override to provide better error handling"""
        return super().get_exception_handler_context()
    
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            return Response({
                'error': str(e),
                'detail': 'Failed to retrieve notification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationMarkReadView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, notification_id):
        obj = Notification.objects.filter(id=notification_id).first()
        if not obj:
            return Response({'error':'not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.mark_as_read()
        return Response({
            'status': 'ok',
            'message': 'تم تحديث الإشعار'
        }, status=status.HTTP_200_OK)


class NotificationResendView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, notification_id):
        obj = Notification.objects.filter(id=notification_id).first()
        if not obj:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Reset status to be resent
            obj.status = 'PROCESSING'
            obj.send_attempts = obj.send_attempts + 1
            obj.save()
            
            # Try to send it again
            notification_service.send_user_notification(
                user_email=obj.user_email,
                action='resent',
                user_name=obj.user_name
            )
            
            obj.status = 'SENT'
            obj.save()
            
            return Response({
                'status': 'ok',
                'message': f'تم إعادة إرسال الإشعار بنجاح (محاولة #{obj.send_attempts})',
                'notification_id': obj.id
            }, status=status.HTTP_200_OK)
        except Exception as e:
            obj.status = 'FAILED'
            obj.error_message = str(e)
            obj.save()
            return Response({
                'error': 'فشل إعادة الإرسال',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationMarkAllReadView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        user_email = request.data.get('user_email')
        qs = Notification.objects.filter(user_email=user_email, is_read=False)
        count = qs.count()
        for n in qs:
            n.mark_as_read()
        return Response({
            'status': 'ok',
            'marked': count,
            'message': f'تم تحديث {count} إشعار'
        }, status=status.HTTP_200_OK)


class NotificationDeleteView(generics.DestroyAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    lookup_url_kwarg = 'notification_id'
    lookup_field = 'id'
    permission_classes = [AllowAny]
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'status': 'ok',
            'message': 'تم حذف الإشعار بنجاح'
        }, status=status.HTTP_200_OK)


class NotificationStatsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        
        # Basic counts
        total = Notification.objects.count()
        sent = Notification.objects.filter(status='SENT').count()
        unread = Notification.objects.filter(is_read=False).count()
        read = Notification.objects.filter(is_read=True).count()
        processing = Notification.objects.filter(status='PROCESSING').count()
        failed = Notification.objects.filter(status='FAILED').count()
        
        # Time-based counts
        now = timezone.now()
        today = Notification.objects.filter(created_at__date=now.date()).count()
        week_ago = now - timedelta(days=7)
        this_week = Notification.objects.filter(created_at__gte=week_ago).count()
        month_ago = now - timedelta(days=30)
        this_month = Notification.objects.filter(created_at__gte=month_ago).count()
        
        return Response({
            'total': total,
            'sent': sent,
            'unread': unread,
            'read': read,
            'processing': processing,
            'failed': failed,
            'today': today,
            'this_week': this_week,
            'this_month': this_month
        })