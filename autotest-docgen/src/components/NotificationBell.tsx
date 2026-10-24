import React, { useState, useEffect, useRef } from 'react';
import { Bell, Check, CheckCircle, Clock, X, Settings, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api.service';
import { useAuth } from '../context/AuthContext';
import { i18n } from '../utils/i18n';
import { ApiErrorHandler } from '../utils/apiErrorHandler';
import { useToast, toastHelpers } from '../components/Toast/Toast';
import './NotificationBell.css';

// Use the Notification type from API service to maintain consistency
type Notification = import('../services/api.service').Notification;

interface NotificationBellProps {
    userId?: string;
}

const NotificationBell: React.FC<NotificationBellProps> = ({ userId }) => {
    const { user } = useAuth();
    const { showToast } = useToast();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();

    // Fetch notifications on component mount and when user changes
    useEffect(() => {
        // Don't fetch if no user email available
        if (!user?.email && !userId) {
            console.log('🔔 No user email available, skipping notification fetch');
            return;
        }

        let isMounted = true;
        const controller = new AbortController();
        let intervalId: number | null = null;
        const requestCountRef = { current: 0 };

        const fetchNotificationsSafe = async () => {
            if (!isMounted) return;

            try {
                const params: any = {};
                // Use user_email instead of user_id to match backend API
                if (user?.email) {
                    params.user_email = user.email;
                } else if (userId) {
                    // Fallback to user_id if available
                    params.user_id = userId;
                }

                console.log('🔔 [', new Date().toISOString(), '] Fetching notifications with params:', params);
                console.log('🔄 Request count:', ++requestCountRef.current);

                const response = await apiService.notifications.getNotifications(params);

                if (!isMounted) return;

                // 🔍 DEBUG: Log complete response structure
                console.log('📥 [', new Date().toISOString(), '] Full API response:', response);
                console.log('📥 Response results:', response.results);
                console.log('📥 Response is array:', Array.isArray(response.results));

                // 🎯 Handle different response structures
                let notificationsList: Notification[] = [];
                let unreadCount = 0;

                if (response.results && Array.isArray(response.results)) {
                    notificationsList = response.results;
                    console.log('✅ Using response.results');
                } else if (Array.isArray(response)) {
                    notificationsList = response;
                    console.log('✅ Using response directly');
                } else {
                    console.warn('⚠️ No valid notifications array found in response');
                }

                // Calculate unread count
                unreadCount = notificationsList.filter((n: Notification) => !n.is_read).length;

                console.log('📊 Final notifications list:', notificationsList);
                console.log('📊 Unread count:', unreadCount);

                // Update state only if component is still mounted
                if (isMounted) {
                    setNotifications(notificationsList);
                    setUnreadCount(unreadCount);
                }

            } catch (error: any) {
                if (!isMounted) return;

                if (error.name !== 'AbortError') {
                    console.error('❌ Error fetching notifications:', error);

                    // Use enhanced error handling with toast notifications
                    const errorDetails = ApiErrorHandler.handle(error, '/api/notifications/');
                    ApiErrorHandler.showError(errorDetails, (message, type) => {
                        showToast(toastHelpers[type](message, 'Failed to load notifications'));
                    });

                    // Set empty array on error to prevent UI issues
                    if (isMounted) {
                        setNotifications([]);
                        setUnreadCount(0);
                    }
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        };

        // Initial fetch
        fetchNotificationsSafe();

        // Set up polling only if explicitly needed (you can disable this for testing)
        // intervalId = window.setInterval(fetchNotificationsSafe, 30000);

        // Cleanup function
        return () => {
            console.log('🧹 NotificationBell cleanup: aborting requests and clearing intervals');
            isMounted = false;
            controller.abort();
            if (intervalId) {
                window.clearInterval(intervalId);
            }
        };
    }, [user?.email, userId]); // Proper dependencies

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // 🎯 Listen for notification update events
    useEffect(() => {
        const handleNotificationUpdate = async (event: Event) => {
            const customEvent = event as CustomEvent;
            console.log('🔔 Received notification-update event:', customEvent.detail);

            // Refetch notifications when event is received
            if (user?.email || userId) {
                try {
                    const params: any = {};
                    if (user?.email) {
                        params.user_email = user.email;
                    } else if (userId) {
                        params.user_id = userId;
                    }

                    console.log('🔄 Refetching notifications due to event:', params);
                    const response = await apiService.notifications.getNotifications(params);

                    // 🔍 DEBUG: Log complete response structure
                    console.log('📥 [EVENT] Full API response:', response);
                    console.log('📥 [EVENT] Response results:', response.results);
                    console.log('📥 [EVENT] Response is array:', Array.isArray(response.results));

                    // 🎯 Handle different response structures
                    let notificationsList: Notification[] = [];
                    let unreadCount = 0;

                    if (response.results && Array.isArray(response.results)) {
                        notificationsList = response.results;
                        console.log('✅ [EVENT] Using response.results');
                    } else if (Array.isArray(response)) {
                        notificationsList = response;
                        console.log('✅ [EVENT] Using response directly');
                    } else {
                        console.warn('⚠️ [EVENT] No valid notifications array found in response');
                    }

                    // Calculate unread count
                    unreadCount = notificationsList.filter((n: Notification) => !n.is_read).length;

                    console.log('📊 [EVENT] Final notifications list:', notificationsList);
                    console.log('📊 [EVENT] Unread count:', unreadCount);

                    // Check for PROJECT_DELETED notifications
                    const projectDeletedNotifications = notificationsList.filter(n =>
                        n.type === 'PROJECT_DELETED' || n.notification_type === 'PROJECT_DELETED'
                    );
                    console.log('🗑️ [EVENT] PROJECT_DELETED notifications found:', projectDeletedNotifications.length);
                    projectDeletedNotifications.forEach(notif => {
                        console.log('🗑️ [EVENT] PROJECT_DELETED notification:', {
                            id: notif.id,
                            title: notif.title,
                            message: notif.message,
                            type: notif.type,
                            notification_type: notif.notification_type,
                            is_read: notif.is_read,
                            created_at: notif.created_at
                        });
                    });

                    setNotifications(notificationsList);
                    setUnreadCount(unreadCount);

                } catch (error) {
                    console.error('❌ [EVENT] Error fetching notifications:', error);
                }
            }
        };

        // Add event listener
        window.addEventListener('notification-update', handleNotificationUpdate);

        // Cleanup
        return () => {
            window.removeEventListener('notification-update', handleNotificationUpdate);
        };
    }, [user?.email, userId]);

    const markAsRead = async (notificationId: string) => {
        try {
            await apiService.notifications.markNotificationAsRead(notificationId);
            setNotifications(prev =>
                prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
            );
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    };

    const markAllAsRead = async () => {
        try {
            const unreadIds = notifications.filter(n => !n.is_read).map(n => n.id);
            if (unreadIds.length === 0) return;

            await apiService.notifications.markAllNotificationsAsRead();
            setNotifications(prev =>
                prev.map(n => ({ ...n, is_read: true }))
            );
            setUnreadCount(0);
        } catch (error) {
            console.error('Failed to mark all notifications as read:', error);
        }
    };

    const deleteNotification = async (notificationId: string) => {
        try {
            await apiService.notifications.deleteNotification(notificationId);
            setNotifications(prev => prev.filter(n => n.id !== notificationId));
            const deletedNotification = notifications.find(n => n.id === notificationId);
            if (deletedNotification && !deletedNotification.is_read) {
                setUnreadCount(prev => Math.max(0, prev - 1));
            }
        } catch (error) {
            console.error('Failed to delete notification:', error);
        }
    };

    const handleNotificationClick = (notification: Notification) => {
        if (!notification.is_read) {
            markAsRead(notification.id);
        }

        if (notification.action_url) {
            navigate(notification.action_url);
            setIsOpen(false);
        }
    };

    const formatTimeAgo = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

        if (diffInSeconds < 60) return i18n.t('notifications.time.now');
        if (diffInSeconds < 3600) return i18n.t('notifications.time.minutes', { count: Math.floor(diffInSeconds / 60) });
        if (diffInSeconds < 86400) return i18n.t('notifications.time.hours', { count: Math.floor(diffInSeconds / 3600) });
        return i18n.t('notifications.time.days', { count: Math.floor(diffInSeconds / 86400) });
    };

    const getNotificationIcon = (type: string) => {
        switch (type) {
            case 'success': return <CheckCircle size={16} className="notification-icon-success" />;
            case 'warning': return <Clock size={16} className="notification-icon-warning" />;
            case 'error': return <X size={16} className="notification-icon-error" />;
            default: return <Clock size={16} className="notification-icon-info" />;
        }
    };

    return (
        <div className="notification-bell-container" ref={dropdownRef}>
            {/* Bell Icon with Badge */}
            <button
                className="notification-bell"
                onClick={() => setIsOpen(!isOpen)}
                title={i18n.t('notifications.title')}
            >
                <Bell size={20} />
            </button>
            {unreadCount > 0 && (
                <span className={`notification-badge${unreadCount >= 10 ? ' badge-multi' : ''}`}>
                    {unreadCount > 99 ? '99+' : unreadCount}
                </span>
            )}

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="notification-dropdown">
                    <div className="notification-header">
                        <h3>{i18n.t('notifications.title')}</h3>
                        <div className="notification-actions">
                            {unreadCount > 0 && (
                                <button
                                    className="mark-all-read-btn"
                                    onClick={markAllAsRead}
                                    title={i18n.t('notifications.markAllRead')}
                                >
                                    <Check size={14} />
                                    {i18n.t('notifications.markAllRead')}
                                </button>
                            )}
                            <button
                                className="view-all-btn"
                                onClick={() => {
                                    navigate('/notifications');
                                    setIsOpen(false);
                                }}
                                title={i18n.t('notifications.viewAll')}
                            >
                                <Settings size={14} />
                                {i18n.t('notifications.viewAll')}
                            </button>
                        </div>
                    </div>

                    <div className="notification-list">
                        {isLoading ? (
                            <div className="notification-loading">
                                <div className="spinner"></div>
                                <p>{i18n.t('notifications.loading')}</p>
                            </div>
                        ) : notifications.length === 0 ? (
                            <div className="notification-empty">
                                <Bell size={32} className="empty-icon" />
                                <p>{i18n.t('notifications.empty')}</p>
                            </div>
                        ) : (
                            notifications.slice(0, 10).map((notification) => (
                                <div
                                    key={notification.id}
                                    className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                                    onClick={() => handleNotificationClick(notification)}
                                >
                                    <div className="notification-content">
                                        <div className="notification-icon">
                                            {getNotificationIcon(notification.type)}
                                        </div>
                                        <div className="notification-text">
                                            <h4 className="notification-title">
                                                {notification.title}
                                                {!notification.is_read && (
                                                    <span className="unread-indicator"></span>
                                                )}
                                            </h4>
                                            <p className="notification-message">
                                                {notification.message}
                                            </p>
                                            <span className="notification-time">
                                                {formatTimeAgo(notification.created_at)}
                                            </span>
                                        </div>
                                        <div className="notification-controls">
                                            {!notification.is_read && (
                                                <button
                                                    className="mark-read-btn"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        markAsRead(notification.id);
                                                    }}
                                                    title={i18n.t('notifications.markRead')}
                                                >
                                                    <Check size={12} />
                                                </button>
                                            )}
                                            <button
                                                className="delete-notification-btn"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    deleteNotification(notification.id);
                                                }}
                                                title={i18n.t('notifications.delete')}
                                            >
                                                <Trash2 size={12} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {notifications.length > 10 && (
                        <div className="notification-footer">
                            <button
                                className="view-all-footer-btn"
                                onClick={() => {
                                    navigate('/notifications');
                                    setIsOpen(false);
                                }}
                            >
                                {i18n.t('notifications.viewAll')} ({notifications.length})
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default NotificationBell;
