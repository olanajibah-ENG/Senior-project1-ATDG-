/**
 * Enhanced API Error Handler Utility
 * Provides consistent error handling across the application
 */

export interface ApiErrorDetails {
  status?: number;
  statusText?: string;
  message: string;
  endpoint: string;
  timestamp: string;
  details?: any;
}

export class ApiErrorHandler {
  /**
   * Handle API errors with detailed logging and user-friendly messages
   */
  static handle(error: any, endpoint: string): ApiErrorDetails {
    const timestamp = new Date().toISOString();
    
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const { status, statusText, data } = error.response;
      
      console.error('API Error Response:', {
        status,
        statusText,
        data,
        endpoint,
        timestamp
      });

      let message = 'An error occurred';
      
      switch (status) {
        case 400:
          message = 'Bad request - Please check your input';
          break;
        case 401:
          message = 'Authentication required - Please log in again';
          break;
        case 403:
          message = 'Access forbidden - You don\'t have permission';
          break;
        case 404:
          message = 'Resource not found - The requested endpoint doesn\'t exist';
          console.warn(`⚠️ Endpoint not found: ${endpoint} - Check API configuration`);
          break;
        case 429:
          message = 'Too many requests - Please try again later';
          break;
        case 500:
          message = 'Server error - Please try again later';
          break;
        case 502:
          message = 'Service temporarily unavailable';
          break;
        case 503:
          message = 'Service maintenance in progress';
          break;
        default:
          message = data?.detail || data?.message || statusText || 'Unknown error occurred';
      }

      return {
        status,
        statusText,
        message,
        endpoint,
        timestamp,
        details: data
      };
    } else if (error.request) {
      // The request was made but no response was received
      console.error('API Network Error:', {
        message: error.message,
        endpoint,
        timestamp
      });

      return {
        message: 'Network error - Please check your connection',
        endpoint,
        timestamp,
        details: { networkError: true, originalMessage: error.message }
      };
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('API Setup Error:', {
        message: error.message,
        stack: error.stack,
        endpoint,
        timestamp
      });

      return {
        message: error.message || 'An unexpected error occurred',
        endpoint,
        timestamp,
        details: { setupError: true, stack: error.stack }
      };
    }
  }

  /**
   * Log API request details for debugging
   */
  static logRequest(method: string, url: string, data?: any, headers?: any) {
    console.log('API Request:', {
      method: method.toUpperCase(),
      url,
      data: data ? JSON.stringify(data, null, 2) : 'No data',
      headers: headers ? JSON.stringify(headers, null, 2) : 'Default headers',
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Log API response details for debugging
   */
  static logResponse(status: number, url: string, data?: any, responseTime?: number) {
    console.log('API Response:', {
      status,
      url,
      data: data ? JSON.stringify(data, null, 2) : 'No data',
      responseTime: responseTime ? `${responseTime}ms` : 'N/A',
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Show user-friendly error message (can be integrated with toast notifications)
   */
  static showError(errorDetails: ApiErrorDetails, showToast?: (message: string, type: 'error' | 'warning' | 'info') => void) {
    const { message, status, endpoint } = errorDetails;
    
    // Log to console for debugging
    console.error('🚨 API Error:', errorDetails);
    
    // Show toast notification if callback provided
    if (showToast) {
      const toastType = status && status >= 500 ? 'error' : 'warning';
      showToast(message, toastType);
    }
    
    // You can also integrate with other notification systems here
    return message;
  }
}

/**
 * Enhanced fetch wrapper with error handling and logging
 */
export async function safeFetch(url: string, options?: RequestInit): Promise<Response> {
  const startTime = Date.now();
  const method = options?.method || 'GET';
  
  // Log request
  ApiErrorHandler.logRequest(method, url, options?.body, options?.headers);
  
  try {
    const response = await fetch(url, options);
    const responseTime = Date.now() - startTime;
    
    // Log response
    ApiErrorHandler.logResponse(response.status, url, null, responseTime);
    
    // Handle error responses
    if (!response.ok) {
      const error = new Error(response.statusText);
      (error as any).response = {
        status: response.status,
        statusText: response.statusText,
        data: await response.text().catch(() => 'Unable to read error response')
      };
      throw error;
    }
    
    return response;
  } catch (error) {
    const responseTime = Date.now() - startTime;
    console.error('API Request Failed:', {
      url,
      method,
      responseTime: `${responseTime}ms`,
      error: error instanceof Error ? error.message : error
    });
    throw error;
  }
}

/**
 * Retry logic for failed requests
 */
export async function retryRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000,
  backoff: number = 2
): Promise<T> {
  let lastError: any;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) {
        console.error(`❌ Request failed after ${maxRetries} attempts:`, error);
        throw lastError;
      }
      
      const waitTime = delay * Math.pow(backoff, attempt - 1);
      console.warn(`⚠️ Request failed (attempt ${attempt}/${maxRetries}), retrying in ${waitTime}ms...`);
      
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }
  
  throw lastError;
}
