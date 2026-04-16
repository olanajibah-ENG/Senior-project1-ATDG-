import React, { useState, type ChangeEvent } from 'react';
import { X, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';

interface ChangePasswordModalProps {
    isOpen: boolean;
    onClose: () => void;
    isLoading: boolean;
}

const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({ 
    isOpen, 
    onClose, 
    isLoading 
}) => {
    const [formData, setFormData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        strength: 'weak'
    });

    const [showPasswords, setShowPasswords] = useState({
        current: false,
        new: false,
        confirm: false
    });

    const [message, setMessage] = useState<{
        type: 'success' | 'error' | null;
        text: string;
    }>({ type: null, text: '' });

    const checkPasswordStrength = (password: string) => {
        if (password.length < 8) return 'weak';
        if (!/\d/.test(password)) return 'weak';
        if (!/[A-Z]/.test(password)) return 'medium';
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) return 'strong';
        return 'medium';
    };

    const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => {
            const newData = { ...prev, [name]: value };
            if (name === 'newPassword') {
                newData.strength = checkPasswordStrength(value);
            }
            return newData;
        });
    };

    const togglePasswordVisibility = (field: 'current' | 'new' | 'confirm') => {
        setShowPasswords(prev => ({
            ...prev,
            [field]: !prev[field]
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        // Validation
        if (!formData.currentPassword) {
            setMessage({ type: 'error', text: 'Current password is required' });
            return;
        }
        
        if (formData.newPassword.length < 8) {
            setMessage({ type: 'error', text: 'Password must be at least 8 characters long' });
            return;
        }
        
        if (formData.newPassword !== formData.confirmPassword) {
            setMessage({ type: 'error', text: 'Passwords do not match' });
            return;
        }

        try {
            // TODO: Add API call to change password
            console.log('Changing password:', {
                current: formData.currentPassword,
                new: formData.newPassword
            });
            
            setMessage({ type: 'success', text: 'Password changed successfully' });
            
            // Close modal after success
            setTimeout(() => {
                onClose();
                // Reset form
                setFormData({
                    currentPassword: '',
                    newPassword: '',
                    confirmPassword: '',
                    strength: 'weak'
                });
                setMessage({ type: null, text: '' });
            }, 2000);
            
        } catch (error) {
            setMessage({ type: 'error', text: 'Failed to change password' });
        }
    };

    const getPasswordStrengthColor = () => {
        switch (formData.strength) {
            case 'weak': return '#ef4444';
            case 'medium': return '#f59e0b';
            case 'strong': return '#10b981';
            default: return '#6b7280';
        }
    };

    const getPasswordStrengthText = () => {
        switch (formData.strength) {
            case 'weak': return 'Weak';
            case 'medium': return 'Medium';
            case 'strong': return 'Strong';
            default: return '';
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content change-password-modal" onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className="change-password-header">
                    <h2>Change Password</h2>
                    <button 
                        className="close-btn" 
                        onClick={onClose}
                        title="Close"
                    >
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="change-password-form">
                    {/* Current Password */}
                    <div className="form-group">
                        <label htmlFor="currentPassword">
                            Current Password
                        </label>
                        <div className="password-input-container">
                            <input
                                type={showPasswords.current ? 'text' : 'password'}
                                id="currentPassword"
                                name="currentPassword"
                                value={formData.currentPassword}
                                onChange={handleInputChange}
                                placeholder="Enter current password"
                                required
                            />
                            <button
                                type="button"
                                className="password-toggle-btn"
                                onClick={() => togglePasswordVisibility('current')}
                                title="Toggle password visibility"
                            >
                                {showPasswords.current ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    {/* New Password */}
                    <div className="form-group">
                        <label htmlFor="newPassword">
                            New Password
                        </label>
                        <div className="password-input-container">
                            <input
                                type={showPasswords.new ? 'text' : 'password'}
                                id="newPassword"
                                name="newPassword"
                                value={formData.newPassword}
                                onChange={handleInputChange}
                                placeholder="Enter new password"
                                required
                            />
                            <button
                                type="button"
                                className="password-toggle-btn"
                                onClick={() => togglePasswordVisibility('new')}
                                title="Toggle password visibility"
                            >
                                {showPasswords.new ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                        
                        {/* Password Strength Indicator */}
                        {formData.newPassword && (
                            <div className="password-strength-indicator">
                                <div className="strength-bar">
                                    <div 
                                        className="strength-fill" 
                                        style={{ 
                                            width: formData.strength === 'weak' ? '33%' : 
                                                   formData.strength === 'medium' ? '66%' : '100%',
                                            backgroundColor: getPasswordStrengthColor()
                                        }}
                                    ></div>
                                </div>
                                <span className="strength-text" style={{ color: getPasswordStrengthColor() }}>
                                    {getPasswordStrengthText()}
                                </span>
                            </div>
                        )}
                        
                        {/* Password Requirements */}
                        <div className="password-requirements">
                            <h4>Password Requirements:</h4>
                            <ul>
                                <li className={formData.newPassword.length >= 8 ? 'requirement-met' : 'requirement-unmet'}>
                                    At least 8 characters
                                </li>
                                <li className={/\d/.test(formData.newPassword) ? 'requirement-met' : 'requirement-unmet'}>
                                    Contains at least one number
                                </li>
                                <li className={/[A-Z]/.test(formData.newPassword) ? 'requirement-met' : 'requirement-unmet'}>
                                    Contains at least one uppercase letter
                                </li>
                                <li className={/[!@#$%^&*(),.?":{}|<>]/.test(formData.newPassword) ? 'requirement-met' : 'requirement-unmet'}>
                                    Contains at least one special character
                                </li>
                            </ul>
                        </div>
                    </div>

                    {/* Confirm New Password */}
                    <div className="form-group">
                        <label htmlFor="confirmPassword">
                            Confirm New Password
                        </label>
                        <div className="password-input-container">
                            <input
                                type={showPasswords.confirm ? 'text' : 'password'}
                                id="confirmPassword"
                                name="confirmPassword"
                                value={formData.confirmPassword}
                                onChange={handleInputChange}
                                placeholder="Confirm new password"
                                required
                            />
                            <button
                                type="button"
                                className="password-toggle-btn"
                                onClick={() => togglePasswordVisibility('confirm')}
                                title="Toggle password visibility"
                            >
                                {showPasswords.confirm ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    {/* Message Display */}
                    {message.type && (
                        <div className={`message ${message.type}`}>
                            {message.type === 'success' ? (
                                <CheckCircle size={20} />
                            ) : (
                                <AlertCircle size={20} />
                            )}
                            <span>{message.text}</span>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="change-password-actions">
                        <button 
                            type="button" 
                            className="btn-secondary" 
                            onClick={onClose}
                            disabled={isLoading}
                        >
                            Cancel
                        </button>
                        <button 
                            type="submit" 
                            className="btn-primary" 
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <div className="loading-spinner-small"></div>
                                    Updating...
                                </>
                            ) : (
                                'Update Password'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ChangePasswordModal;
