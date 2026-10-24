import React, { useEffect } from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react';
import './Alert.css';

export type AlertType = 'success' | 'error' | 'warning' | 'info' | 'confirm';

export interface AlertProps {
    type: AlertType;
    title: string;
    message: string;
    onConfirm?: () => void;
    onCancel?: () => void;
    confirmText?: string;
    cancelText?: string;
    showCancel?: boolean;
    onClose?: () => void;
}

const Alert: React.FC<AlertProps> = ({
    type,
    title,
    message,
    onConfirm,
    onCancel,
    confirmText = 'OK',
    cancelText = 'Cancel',
    showCancel = false,
    onClose,
}) => {
    // Handle Escape key to close
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && onClose) {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [onClose]);

    const getIcon = () => {
        const iconSize = 24;
        switch (type) {
            case 'success':
                return <CheckCircle size={iconSize} className="alert-icon" />;
            case 'error':
                return <AlertCircle size={iconSize} className="alert-icon" />;
            case 'warning':
                return <AlertTriangle size={iconSize} className="alert-icon" />;
            case 'info':
            case 'confirm':
                return <Info size={iconSize} className="alert-icon" />;
            default:
                return null;
        }
    };

    const handleConfirm = () => {
        if (onConfirm) {
            onConfirm();
        }
        if (onClose) {
            onClose();
        }
    };

    const handleCancel = () => {
        if (onCancel) {
            onCancel();
        }
        if (onClose) {
            onClose();
        }
    };

    return (
        <div className="alert-overlay" onClick={onClose}>
            <div className={`alert-container alert-${type}`} onClick={(e) => e.stopPropagation()}>
                {onClose && (
                    <button className="alert-close" onClick={onClose} aria-label="Close">
                        <X size={18} />
                    </button>
                )}
                <div className="alert-header">
                    {getIcon()}
                    <h3 className="alert-title">{title}</h3>
                </div>
                <div className="alert-body">
                    <p className="alert-message">{message}</p>
                </div>
                <div className="alert-actions">
                    {showCancel && (
                        <button
                            type="button"
                            className="alert-btn alert-btn-cancel"
                            onClick={handleCancel}
                        >
                            {cancelText}
                        </button>
                    )}
                    <button
                        type="button"
                        className={`alert-btn alert-btn-${type === 'confirm' ? 'confirm' : 'primary'}`}
                        onClick={handleConfirm}
                        autoFocus
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Alert;

