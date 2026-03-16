import React from 'react';
import './LoadingSpinner.css'; // استيراد ملف التنسيقات

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large'; // تحديد حجم الدوارة
  message?: string; // رسالة اختيارية تظهر أسفل الدوارة
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'medium', message }) => {
  // تحديد اسم الكلاس بناءً على الحجم
  const spinnerClass = `spinner-container spinner-${size}`; 

  return (
    <div className={spinnerClass}>
      <div className="spinner"></div>
      {/* عرض رسالة اختيارية إذا كانت موجودة */}
      {message && <p className="loading-message">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;