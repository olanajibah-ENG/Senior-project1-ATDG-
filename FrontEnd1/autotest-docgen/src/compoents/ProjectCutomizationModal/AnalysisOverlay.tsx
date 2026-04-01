import React, { useEffect, useState } from 'react';
import './LoadingSpinner.css';

interface AnalysisOverlayProps {
  message?: string;
}

const steps = [
  { icon: '📦', label: 'Uploading files...' },
  { icon: '🔍', label: 'Analyzing code structure...' },
  { icon: '🧩', label: 'Extracting classes & relationships...' },
  { icon: '📊', label: 'Building class diagram...' },
  { icon: '✅', label: 'Finalizing results...' },
];

const AnalysisOverlay: React.FC<AnalysisOverlayProps> = ({ message }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Advance steps every ~4s
    const stepInterval = setInterval(() => {
      setCurrentStep(s => (s < steps.length - 1 ? s + 1 : s));
    }, 4000);

    // Smooth progress bar
    const progressInterval = setInterval(() => {
      setProgress(p => (p < 92 ? p + 1 : p));
    }, 300);

    return () => {
      clearInterval(stepInterval);
      clearInterval(progressInterval);
    };
  }, []);

  return (
    <div className="analysis-overlay">
      <div className="analysis-overlay-content" style={{ minWidth: 360, maxWidth: 480 }}>

        {/* Animated rings */}
        <div style={{ position: 'relative', width: 90, height: 90, margin: '0 auto 24px' }}>
          <div style={{
            position: 'absolute', inset: 0, borderRadius: '50%',
            border: '3px solid rgba(118,75,162,0.15)',
            animation: 'ultraSpin 3s linear infinite reverse',
          }} />
          <div style={{
            position: 'absolute', inset: 8, borderRadius: '50%',
            border: '3px solid transparent',
            borderTop: '3px solid #c084fc',
            borderRight: '3px solid #667eea',
            animation: 'ultraSpin 1.2s linear infinite',
          }} />
          <div style={{
            position: 'absolute', inset: 18, borderRadius: '50%',
            border: '3px solid transparent',
            borderTop: '3px solid #f093fb',
            animation: 'ultraSpin 0.8s linear infinite reverse',
          }} />
          {/* Center icon */}
          <div style={{
            position: 'absolute', inset: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 26,
          }}>
            {steps[currentStep].icon}
          </div>
        </div>

        {/* Title */}
        <h3 style={{
          margin: '0 0 8px',
          background: 'linear-gradient(135deg,#667eea,#764ba2,#f093fb)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          backgroundClip: 'text', fontSize: '1.3rem', fontWeight: 700,
        }}>
          Analyzing Project
        </h3>

        {/* Current step label */}
        <p style={{
          margin: '0 0 20px', color: '#a78bca',
          fontSize: '0.95rem', fontWeight: 500,
          minHeight: 22, transition: 'all 0.4s ease',
        }}>
          {steps[currentStep].label}
        </p>

        {/* Progress bar */}
        <div style={{
          width: '100%', height: 6,
          background: 'rgba(118,75,162,0.15)',
          borderRadius: 3, overflow: 'hidden', marginBottom: 20,
        }}>
          <div style={{
            height: '100%', borderRadius: 3,
            background: 'linear-gradient(90deg,#667eea,#764ba2,#f093fb)',
            width: `${progress}%`,
            transition: 'width 0.3s ease',
            position: 'relative',
          }}>
            <div style={{
              position: 'absolute', inset: 0,
              background: 'linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent)',
              animation: 'progressShimmer 1.5s ease-in-out infinite',
            }} />
          </div>
        </div>

        {/* Steps dots */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8 }}>
          {steps.map((_, i) => (
            <div key={i} style={{
              width: i === currentStep ? 20 : 8,
              height: 8, borderRadius: 4,
              background: i <= currentStep
                ? 'linear-gradient(90deg,#667eea,#764ba2)'
                : 'rgba(118,75,162,0.20)',
              transition: 'all 0.4s ease',
            }} />
          ))}
        </div>

        {/* Custom message if provided */}
        {message && message !== 'Processing code, please wait...' && (
          <p style={{
            marginTop: 16, fontSize: '0.85rem',
            color: 'rgba(167,139,202,0.7)', fontStyle: 'italic',
          }}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
};

export default AnalysisOverlay;
