/**
 * Custom hook for API calls with retry logic and enhanced error handling
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { ApiErrorHandler, retryRequest } from '../utils/apiErrorHandler';

interface UseApiWithRetryOptions {
  maxRetries?: number;
  delay?: number;
  backoff?: number;
  showToast?: (message: string, type: 'error' | 'warning' | 'info') => void;
}

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export function useApiWithRetry<T = any>(options: UseApiWithRetryOptions = {}) {
  const {
    maxRetries = 3,
    delay = 1000,
    backoff = 2,
    showToast
  } = options;

  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
    lastUpdated: null
  });

  const execute = useCallback(async (
    apiCall: () => Promise<T>,
    endpoint?: string
  ): Promise<T | null> => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await retryRequest(apiCall, maxRetries, delay, backoff);

      setState({
        data: result,
        loading: false,
        error: null,
        lastUpdated: new Date()
      });

      return result;
    } catch (error) {
      const errorDetails = ApiErrorHandler.handle(error, endpoint || 'unknown');
      const errorMessage = ApiErrorHandler.showError(errorDetails, showToast);

      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));

      return null;
    }
  }, [maxRetries, delay, backoff, showToast]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      lastUpdated: null
    });
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    execute,
    reset,
    clearError
  };
}

/**
 * Specific hook for notifications with polling
 */
export function useNotificationsPolling(pollInterval: number = 30000) {
  const api = useApiWithRetry<any[]>({ maxRetries: 2 });
  const [isPolling, setIsPolling] = useState(false);
  const pollTimeoutRef = useRef<number | undefined>(undefined);

  const startPolling = useCallback((fetchFunction: () => Promise<any[]>) => {
    setIsPolling(true);

    const poll = async () => {
      await api.execute(fetchFunction, '/api/notifications/');

      if (isPolling) {
        pollTimeoutRef.current = window.setTimeout(poll, pollInterval);
      }
    };

    poll();
  }, [api, pollInterval, isPolling]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
    if (pollTimeoutRef.current) {
      window.clearTimeout(pollTimeoutRef.current);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollTimeoutRef.current) {
        window.clearTimeout(pollTimeoutRef.current);
      }
    };
  }, []);

  return {
    ...api,
    isPolling,
    startPolling,
    stopPolling
  };
}
