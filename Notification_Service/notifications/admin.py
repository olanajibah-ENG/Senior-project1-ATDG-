"""
Admin configuration for Notification models
"""
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Notification model
    """
    list_display = [
        'id',
        'title',
        'user_email',
        'user_name',
        'notification_type',
        'status',
        'is_read',
        'priority',
        'created_at',
    ]
    
    list_filter = [
        'notification_type',
        'status',
        'is_read',
        'priority',
        'created_at',
        'email_sent',
    ]
    
    search_fields = [
        'title',
        'message',
        'user_email',
        'user_name',
        'user_id',
        'related_id',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'sent_at',
        'read_at',
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user_email', 'user_name', 'user_id')
        }),
        ('Notification Content', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('Related Information', {
            'fields': ('related_id', 'related_type', 'action_url', 'action_text'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'is_read', 'email_sent', 'send_attempts')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'read_at'),
            'classes': ('collapse',)
        }),
        ('Extra Data', {
            'fields': ('extra_data',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    actions = ['mark_as_read', 'mark_as_unread', 'mark_as_sent']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        count = queryset.update(is_read=True, status='READ')
        self.message_user(request, f'{count} notification(s) marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        count = queryset.update(is_read=False)
        self.message_user(request, f'{count} notification(s) marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"
    
    def mark_as_sent(self, request, queryset):
        """Mark selected notifications as sent"""
        from django.utils import timezone
        count = queryset.update(email_sent=True, status='SENT', sent_at=timezone.now())
        self.message_user(request, f'{count} notification(s) marked as sent.')
    mark_as_sent.short_description = "Mark selected notifications as sent"
