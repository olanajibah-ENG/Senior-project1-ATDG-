/**
 * Toast Notification Component
 * Provides consistent error/success/info notifications across the application
 */

import React, { useState, useEffect, createContext, useContext, useCallback } from 'react';
import { X, CheckCircle, AlertCircle, Info, XCircle } from 'lucide-react';
import './Toast.css';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  persistent?: boolean;
}

interface ToastContextType {
  showToast: (message: Omit<ToastMessage, 'id'>) => void;
  removeToast: (id: string) => void;
  clearAllToasts: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((message: Omit<ToastMessage, 'id'>) => {
    const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
    const newToast: ToastMessage = {
      ...message,
      id,
      duration: message.duration ?? (message.type === 'error' ? 5000 : 3000),
    };

    setToasts(prev => [...prev, newToast]);

    // Auto-remove toast after duration (unless persistent)
    if (!newToast.persistent && newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast, removeToast, clearAllToasts }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
};

interface ToastContainerProps {
  toasts: ToastMessage[];
  onRemove: (id: string) => void;
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemove }) => {
  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
};

interface ToastItemProps {
  toast: ToastMessage;
  onRemove: (id: string) => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onRemove }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    const timer = setTimeout(() => setIsVisible(true), 10);
    return () => clearTimeout(timer);
  }, []);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => onRemove(toast.id), 300); // Wait for exit animation
  };

  const getIcon = () => {
    const iconClass = "toast-icon";
    switch (toast.type) {
      case 'success':
        return <CheckCircle className={`${iconClass} toast-icon-success`} size={20} />;
      case 'error':
        return <XCircle className={`${iconClass} toast-icon-error`} size={20} />;
      case 'warning':
        return <AlertCircle className={`${iconClass} toast-icon-warning`} size={20} />;
      case 'info':
        return <Info className={`${iconClass} toast-icon-info`} size={20} />;
      default:
        return <Info className={iconClass} size={20} />;
    }
  };

  return (
    <div
      className={`toast toast-${toast.type} ${isVisible ? 'toast-visible' : 'toast-hidden'}`}
      role="alert"
      aria-live="polite"
    >
      <div className="toast-content">
        {getIcon()}
        <div className="toast-message">
          <div className="toast-title">{toast.title}</div>
          {toast.message && (
            <div className="toast-description">{toast.message}</div>
          )}
        </div>
      </div>
      <button
        className="toast-close"
        onClick={handleClose}
        aria-label="Close notification"
      >
        <X size={16} />
      </button>
    </div>
  );
};

// Convenience functions for common toast types
export const toastHelpers = {
  success: (title: string, message?: string, options?: Partial<Omit<ToastMessage, 'id' | 'type' | 'title' | 'message'>>) => ({
    type: 'success' as const,
    title,
    message,
    ...options,
  }),

  error: (title: string, message?: string, options?: Partial<Omit<ToastMessage, 'id' | 'type' | 'title' | 'message'>>) => ({
    type: 'error' as const,
    title,
    message,
    duration: 5000, // Errors stay longer
    ...options,
  }),

  warning: (title: string, message?: string, options?: Partial<Omit<ToastMessage, 'id' | 'type' | 'title' | 'message'>>) => ({
    type: 'warning' as const,
    title,
    message,
    ...options,
  }),

  info: (title: string, message?: string, options?: Partial<Omit<ToastMessage, 'id' | 'type' | 'title' | 'message'>>) => ({
    type: 'info' as const,
    title,
    message,
    ...options,
  }),
};
