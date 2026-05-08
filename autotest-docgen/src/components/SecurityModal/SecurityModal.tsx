import React from 'react';
import { Shield, Clock, MapPin, Smartphone, Monitor } from 'lucide-react';

interface SecurityModalProps {
    isOpen: boolean;
    onClose: () => void;
    language: 'en' | 'ar';
}

const SecurityModal: React.FC<SecurityModalProps> = ({ isOpen, onClose, language }) => {
    const lastLogin = {
        date: language === 'ar' ? '١٣ فبراير ٢٠٢٦' : 'February 13, 2026',
        time: language === 'ar' ? '٢:١٥ ص' : '2:15 AM',
        device: language === 'ar' ? 'ويندوز - كروم' : 'Windows - Chrome',
        location: language === 'ar' ? 'الرياض، السعودية' : 'Riyadh, Saudi Arabia'
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content security-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <div className="modal-header-content">
                        <Shield className="w-6 h-6 text-blue-500" />
                        <h2 className="modal-title">
                            {language === 'ar' ? 'الأمان' : 'Security'}
                        </h2>
                    </div>
                    <button className="modal-close-btn" onClick={onClose}>
                        ×
                    </button>
                </div>

                <div className="modal-body">
                    <div className="security-section">
                        <h3 className="security-section-title">
                            {language === 'ar' ? 'آخر تسجيل دخول' : 'Last Login'}
                        </h3>
                        <div className="last-login-card">
                            <div className="last-login-item">
                                <Clock className="w-5 h-5 text-gray-500" />
                                <div>
                                    <div className="last-login-label">
                                        {language === 'ar' ? 'التاريخ والوقت' : 'Date & Time'}
                                    </div>
                                    <div className="last-login-value">
                                        {lastLogin.date} - {lastLogin.time}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="modal-footer">
                    <button className="btn btn-primary" onClick={onClose}>
                        {language === 'ar' ? 'إغلاق' : 'Close'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SecurityModal;
