import { useState, useCallback } from 'react';
import Alert from './Alert';
import type { AlertType } from './Alert';

export interface AlertOptions {
    type: AlertType;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    showCancel?: boolean;
}

export interface ConfirmOptions {
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
}

// Hook for managing alert state
export const useAlert = () => {
    const [alert, setAlert] = useState<AlertOptions | null>(null);
    const [resolvePromise, setResolvePromise] = useState<((value: boolean) => void) | null>(null);

    const showAlert = useCallback((options: AlertOptions): Promise<boolean> => {
        return new Promise((resolve) => {
            setAlert(options);
            setResolvePromise(() => resolve);
        });
    }, []);

    const showConfirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
        return showAlert({
            ...options,
            type: 'confirm',
            showCancel: true,
        });
    }, [showAlert]);

    const hideAlert = useCallback((confirmed: boolean = false) => {
        if (resolvePromise) {
            resolvePromise(confirmed);
        }
        setAlert(null);
        setResolvePromise(null);
    }, [resolvePromise]);

    const AlertComponent = alert ? (
        <Alert
            type={alert.type}
            title={alert.title}
            message={alert.message}
            confirmText={alert.confirmText}
            cancelText={alert.cancelText}
            showCancel={alert.showCancel}
            onConfirm={() => hideAlert(true)}
            onCancel={() => hideAlert(false)}
            onClose={() => hideAlert(false)}
        />
    ) : null;

    return {
        showAlert,
        showConfirm,
        hideAlert,
        AlertComponent,
    };
};

