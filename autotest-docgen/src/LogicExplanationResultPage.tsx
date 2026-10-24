import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { type LogicExplanationResponse } from './services/api.service';
import { useLanguage } from './context/LanguageContext';
import './LogicExplanationResultPage.css';

interface LogicExplanationLocationState {
  result: LogicExplanationResponse;
  projectId: string;
}

const LogicExplanationResultPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { language } = useLanguage();
  const state = (location.state || {}) as LogicExplanationLocationState;
  const { result } = state;

  if (!result) {
    return (
      <div className="dashboard-layout" style={{ padding: '24px' }}>
        <button
          onClick={() => navigate('/dashboard')}
          className="btn-secondary"
          style={{ marginBottom: '16px', display: 'inline-flex', alignItems: 'center' }}
        >
          <ArrowLeft size={16} style={{ marginRight: 6 }} /> Back to Dashboard
        </button>

        <div className="error-message" style={{ marginTop: 16 }}>
          No explanation data found. Please generate an explanation first.
        </div>
      </div>
    );
  }

  const formatExplanationText = (text: string) => {
    if (language === 'en') {
      // English formatting - simple text display
      const paragraphs = text.split('\n\n').filter(p => p.trim());

      const headerKeywords = ['Strategic Overview', 'Key Capabilities', 'Business Value', 'System Overview', 'Core Entities', 'How It Works Together'];

      return paragraphs.map((para, idx) => {
        const trimmed = para.trim();
        const lines = trimmed.split('\n').map(l => l.trim()).filter(Boolean);

        // Detect AI-generated section headers and style them
        const firstLine = lines[0] || '';
        const matchedHeader = headerKeywords.find(h => firstLine.toLowerCase().startsWith(h.toLowerCase()));
        if (matchedHeader) {
          const body = lines.slice(1).join(' ');
          return (
            <div key={idx} style={{ marginBottom: '20px' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--accent-color, #0f172a)' }}>{matchedHeader}</h2>
              <p style={{ marginTop: '8px', lineHeight: '1.7', fontSize: '1rem' }}>{body}</p>
            </div>
          );
        }

        // Check if this paragraph contains bullet points
        if (trimmed.includes('*')) {
          const bulletLines = trimmed.split('\n').filter(line => line.trim().startsWith('*'));
          return (
            <div key={idx} style={{ marginBottom: '20px' }}>
              {bulletLines.map((bullet, bulletIdx) => {
                const bulletText = bullet.trim().replace(/^\*\s*/, '');
                const colonIndex = bulletText.indexOf(':');
                if (colonIndex > 0 && colonIndex < 50) {
                  const key = bulletText.substring(0, colonIndex).trim();
                  const value = bulletText.substring(colonIndex + 1).trim();
                  return (
                    <p key={bulletIdx} style={{
                      marginBottom: '12px',
                      lineHeight: '1.7',
                      fontSize: '1rem',
                      paddingLeft: '20px'
                    }}>
                      <strong>{key}:</strong> {value}
                    </p>
                  );
                }
                return (
                  <p key={bulletIdx} style={{
                    marginBottom: '12px',
                    lineHeight: '1.7',
                    fontSize: '1rem',
                    paddingLeft: '20px'
                  }}>
                    {bulletText}
                  </p>
                );
              })}
            </div>
          );
        }

        // Regular paragraph
        return (
          <p key={idx} style={{
            marginBottom: '20px',
            lineHeight: '1.7',
            fontSize: '1rem'
          }}>
            {trimmed}
          </p>
        );
      });
    } else {
      // Arabic formatting
      return text.split('\n\n').map((paragraph, index) => (
        <p key={index} style={{
          marginBottom: '20px',
          lineHeight: '1.7',
          textAlign: 'right',
          direction: 'rtl',
          fontSize: '1rem'
        }}>
          {paragraph.split('\n').map((line, lineIndex) => (
            <span key={lineIndex}>
              {line}
              {lineIndex < paragraph.split('\n').length - 1 && <br />}
            </span>
          ))}
        </p>
      ));
    }
  };

  return (
    <div className="dashboard-layout" style={{ 
      padding: '24px', 
      maxWidth: '100%',
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh'
    }}>
      <button
        onClick={() => navigate('/dashboard')}
        className="btn-secondary"
        style={{
          marginBottom: '24px',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          alignSelf: 'flex-start'
        }}
      >
        <ArrowLeft size={16} />
        Back to Dashboard
      </button>

      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '100%'
      }}>
        <div style={{
          background: 'var(--card-bg, #fff)',
          borderRadius: 12,
          padding: 40,
          boxShadow: '0 6px 18px rgba(0,0,0,0.06)',
          width: '100%',
          maxWidth: '900px',
          margin: '0 auto'
        }}>
          <div style={{
            color: 'var(--text-color, #1f2937)',
            fontSize: '1rem',
            lineHeight: '1.7'
          }}>
            {formatExplanationText(result.explanation)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogicExplanationResultPage;
