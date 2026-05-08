import { API_ENDPOINTS } from '../config/api.config';

export interface NotificationDetails {
  projectName?: string;
  projectId?: string;
  codeName?: string;
  codeId?: string;
  fileName?: string;
  fileType?: string;
  explanationLevel?: string;
}

/**
 * Unified notification helper function to avoid duplication
 */
export const sendNotification = async (
  user: any,
  type: 'project' | 'code' | 'documentation' | 'explanation' | 'document',
  action: string,
  details: NotificationDetails
) => {
  try {
    // Get user data
    const userEmail = user?.email || localStorage.getItem('user_email') || 'user@example.com';
    const userName = user?.username || localStorage.getItem('user_name') || 'User';

    const notificationData: any = {
      user_email: userEmail,
      user_name: userName,
      user_id: user?.id || localStorage.getItem('user_id') || '',
      action: action,
      project_name: details.projectName || 'Unknown Project',
    };

    // Build data based on type
    if (type === 'project') {
      notificationData.project_name = details.projectName;
      notificationData.project_id = details.projectId;
    } else if (type === 'code') {
      notificationData.code_name = details.codeName;
      notificationData.code_id = details.codeId;
    } else if (type === 'documentation' || type === 'explanation' || type === 'document') {
      notificationData.file_name = details.fileName || `${type}_${Date.now()}`;
      notificationData.file_type = details.fileType || type;
      if (type === 'explanation' && details.explanationLevel) {
        notificationData.explanation_level = details.explanationLevel;
      }
    }

    // Get auth headers
    const getAuthHeaders = () => {
      const headers: any = {
        'Content-Type': 'application/json',
      };

      const token = localStorage.getItem('access_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      return headers;
    };

    // Call notification API
    const endpoint = type === 'project' ? 'project' : type === 'code' ? 'code' : 'documentation';
    const response = await fetch(API_ENDPOINTS.notifications[endpoint](), {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify(notificationData)
    });

    if (response.ok) {
      console.log(`✅ Notification sent for ${type} ${action}`);
    } else {
      console.warn(`⚠️ Failed to send notification for ${type} ${action}`);
    }
  } catch (error) {
    console.error('❌ Error sending notification:', error);
  }
};
