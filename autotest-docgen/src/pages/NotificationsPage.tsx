import React, { useState, useEffect } from 'react';
import { Bell, Check, Trash2, Clock, CheckCircle, X, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api.service';
import { useLanguage } from '../context/LanguageContext';
import { i18n } from '../utils/i18n';
import './NotificationsPage.css';

// Use the Notification type from API service to maintain consistency
type Notification = import('../services/api.service').Notification;

const NotificationsPage: React.FC = () => {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();
    const { } = useLanguage();

    useEffect(() => {
        let isMounted = true;
        const controller = new AbortController();

        const fetchAllNotificationsSafe = async () => {
            if (!isMounted) return;

            try {
                setIsLoading(true);
                setError(null);

                // Get user from AuthContext or localStorage
                const userStr = localStorage.getItem('user');
                const user = userStr ? JSON.parse(userStr) : null;

                const params: any = {};
                if (user?.email) {
                    params.user_email = user.email;
                }

                console.log('🔔 NotificationsPage: [', new Date().toISOString(), '] Fetching with params:', params);
                const response = await apiService.notifications.getNotifications(params);

                if (!isMounted) return;

                // 🔍 DEBUG: Log complete response structure
                console.log('📥 NotificationsPage [', new Date().toISOString(), '] Full response:', response);
                console.log('📥 NotificationsPage Results:', response.results);
                console.log('📥 NotificationsPage is array:', Array.isArray(response.results));

                // 🎯 Handle different response structures
                let notificationsList: Notification[] = [];

                if (response.results && Array.isArray(response.results)) {
                    notificationsList = response.results;
                    console.log('✅ Using response.results');
                } else if (Array.isArray(response)) {
                    notificationsList = response;
                    console.log('✅ Using response directly');
                } else {
                    console.warn('⚠️ No valid notifications array found');
                }

                console.log('📊 NotificationsPage Final notifications list:', notificationsList);

                // Update state only if component is still mounted
                if (isMounted) {
                    setNotifications(notificationsList);
                }

            } catch (err: any) {
                if (!isMounted) return;

                if (err.name !== 'AbortError') {
                    console.error('❌ NotificationsPage Error fetching notifications:', err);
                    setError('Failed to load notifications');
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        };

        fetchAllNotificationsSafe();

        // Cleanup function
        return () => {
            console.log('🧹 NotificationsPage cleanup: aborting requests');
            isMounted = false;
            controller.abort();
        };
    }, []); // Empty dependency array - run only once on mount

    const markAsRead = async (notificationId: string) => {
        try {
            await apiService.notifications.markNotificationAsRead(notificationId);
            setNotifications(prev =>
                prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
            );
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
        } catch (error) {
            console.error('Failed to mark all notifications as read:', error);
        }
    };

    const deleteNotification = async (notificationId: string) => {
        try {
            await apiService.notifications.deleteNotification(notificationId);
            setNotifications(prev => prev.filter(n => n.id !== notificationId));
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
            case 'success': return <CheckCircle size={20} className="notification-type-icon success" />;
            case 'warning': return <Clock size={20} className="notification-type-icon warning" />;
            case 'error': return <X size={20} className="notification-type-icon error" />;
            default: return <Clock size={20} className="notification-type-icon info" />;
        }
    };

    const unreadCount = notifications.filter(n => !n.is_read).length;

    return (
        <div className="notifications-page">
            {/* Header */}
            <div className="notifications-header">
                <div className="header-left">
                    <button
                        className="back-btn"
                        onClick={() => navigate('/dashboard')}
                        title={i18n.t('common.back')}
                    >
                        <ArrowLeft size={20} />
                        {i18n.t('common.back')}
                    </button>
                    <h1>
                        <Bell size={24} className="header-icon" />
                        {i18n.t('notifications.all')}
                    </h1>
                </div>
                <div className="header-actions">
                    {unreadCount > 0 && (
                        <button
                            className="mark-all-read-btn"
                            onClick={markAllAsRead}
                        >
                            <Check size={16} />
                            {i18n.t('notifications.markAllRead')} ({unreadCount})
                        </button>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="notifications-content">
                {isLoading ? (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>{i18n.t('notifications.loading')}</p>
                    </div>
                ) : error ? (
                    <div className="error-state">
                        <X size={48} className="error-icon" />
                        <h3>{i18n.t('common.error')}</h3>
                        <p>{error}</p>
                        <button onClick={() => window.location.reload()} className="retry-btn">
                            {i18n.t('common.retry')}
                        </button>
                    </div>
                ) : notifications.length === 0 ? (
                    <div className="empty-state">
                        <Bell size={64} className="empty-icon" />
                        <h3>{i18n.t('notifications.empty')}</h3>
                        <p>{i18n.t('notifications.emptyDescription')}</p>
                    </div>
                ) : (
                    <div className="notifications-list">
                        {notifications.map((notification) => (
                            <div
                                key={notification.id}
                                className={`notification-card ${!notification.is_read ? 'unread' : ''}`}
                                onClick={() => handleNotificationClick(notification)}
                            >
                                <div className="notification-card-content">
                                    <div className="notification-icon">
                                        {getNotificationIcon(notification.type)}
                                    </div>
                                    <div className="notification-details">
                                        <h3 className="notification-title">
                                            {notification.title}
                                            {!notification.is_read && (
                                                <span className="unread-dot"></span>
                                            )}
                                        </h3>
                                        <p className="notification-message">
                                            {notification.message}
                                        </p>
                                        <div className="notification-meta">
                                            <span className="notification-time">
                                                <Clock size={14} />
                                                {formatTimeAgo(notification.created_at)}
                                            </span>
                                            {notification.action_text && (
                                                <span className="action-text">
                                                    {notification.action_text}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="notification-actions">
                                        {!notification.is_read && (
                                            <button
                                                className="action-btn mark-read"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    markAsRead(notification.id);
                                                }}
                                                title={i18n.t('notifications.markRead')}
                                            >
                                                <Check size={16} />
                                            </button>
                                        )}
                                        <button
                                            className="action-btn delete"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                deleteNotification(notification.id);
                                            }}
                                            title={i18n.t('notifications.delete')}
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default NotificationsPage;
