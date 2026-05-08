"""
Serializers للإشعارات
AutoTest & DocGen Notification Service
"""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer للإشعارات - للقراءة والكتابة
    """
    type = serializers.CharField(source='notification_type', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'user_email',
            'user_name',
            'user_id',
            'title',
            'message',
            'type',
            'notification_type',
            'related_id',
            'related_type',
            'status',
            'priority',
            'action_url',
            'action_text',
            'is_read',
            'read_at',
            'created_at',
            'sent_at',
            'email_sent',
            'extra_data',
        ]
        read_only_fields = ['id', 'created_at', 'sent_at', 'read_at']
    
    def to_representation(self, instance):
        """Override to handle null values gracefully"""
        data = super().to_representation(instance)
        # Remove null values for cleaner response
        return {k: v for k, v in data.items() if v is not None}


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء إشعار جديد
    """
    class Meta:
        model = Notification
        fields = [
            'user_email',
            'user_name',
            'user_id',
            'title',
            'message',
            'notification_type',
            'related_id',
            'related_type',
            'priority',
            'action_url',
            'action_text',
            'extra_data',
        ]


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer لتحديث إشعار (مثل mark as read)
    """
    class Meta:
        model = Notification
        fields = ['is_read']


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer مبسط لقائمة الإشعارات مع معالجة أفضل للقيم الفارغة
    """
    type = serializers.CharField(source='notification_type', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'type',
            'is_read',
            'created_at',
            'action_url',
            'action_text',
        ]
    
    def to_representation(self, instance):
        """Override to handle null values gracefully and provide defaults"""
        try:
            data = super().to_representation(instance)
            
            # Handle null values with sensible defaults
            if data.get('action_url') is None:
                data['action_url'] = ''
            if data.get('action_text') is None:
                data['action_text'] = ''
                
            # Ensure created_at is in ISO format
            if data.get('created_at'):
                data['created_at'] = instance.created_at.isoformat()
            
            return data
            
        except Exception as e:
            # Log error and return minimal safe data
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in NotificationListSerializer.to_representation: {str(e)}", exc_info=True)
            
            # Return minimal safe data
            return {
                'id': instance.id,
                'title': getattr(instance, 'title', 'Unknown Notification'),
                'message': getattr(instance, 'message', ''),
                'type': getattr(instance, 'notification_type', 'CUSTOM'),
                'is_read': getattr(instance, 'is_read', False),
                'created_at': getattr(instance, 'created_at', None),
                'action_url': '',
                'action_text': '',
            }


class SimpleNotificationResponseSerializer(serializers.Serializer):
    """
    Serializer للاستجابة عند إرسال إشعار (للتوافق مع الكود القديم)
    """
    message = serializers.CharField()
    status = serializers.CharField()
    type = serializers.CharField(required=False)
    title = serializers.CharField(required=False)


class NotificationSettingsSerializer(serializers.Serializer):
    """
    Serializer لإعدادات الإشعارات
    """
    email_enabled = serializers.BooleanField(default=True)
    notification_types_enabled = serializers.DictField(
        child=serializers.BooleanField(),
        default=dict
    )
    email_frequency = serializers.ChoiceField(
        choices=[
            ('immediate', 'فوري'),
            ('daily', 'يومي'),
            ('weekly', 'أسبوعي'),
        ],
        default='immediate'
    )
    storage_type = serializers.CharField(default='database')
    description = serializers.CharField(required=False)
