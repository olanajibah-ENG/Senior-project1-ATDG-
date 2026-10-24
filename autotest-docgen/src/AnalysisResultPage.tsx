import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

interface AnalysisLocationState {
  projectId: string;
  codeName: string;
  fileName: string;
  result: {
    summary: string;
    metrics?: {
      linesOfCode?: number;
      language?: string;
      version?: string;
    };
  };
}

const AnalysisResultPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state || {}) as AnalysisLocationState;

  const { codeName, fileName, result } = state;

  return (
    <div className="dashboard-layout" style={{ padding: '24px' }}>
      <button
        onClick={() => navigate('/dashboard')}
        className="btn-secondary"
        style={{ display: 'inline-flex', alignItems: 'center', marginBottom: '16px' }}
      >
        <ArrowLeft size={16} style={{ marginRight: 6 }} /> Back to Dashboard
      </button>

      <h2 style={{ marginBottom: '8px' }}>Code Analysis Result</h2>
      <p style={{ marginBottom: '16px', color: 'var(--secondary-color)' }}>
        {codeName && <strong>{codeName}</strong>} {fileName && <>({fileName})</>}
      </p>

      {result ? (
        <div
          style={{
            background: 'var(--card-bg, #fff)',
            borderRadius: 12,
            padding: 20,
            boxShadow: '0 6px 18px rgba(0,0,0,0.06)',
          }}
        >
          <h3 style={{ marginTop: 0, marginBottom: 12 }}>Summary</h3>
          <p style={{ marginBottom: 16 }}>{result.summary}</p>

          {result.metrics && (
            <>
              <h4 style={{ marginBottom: 8 }}>Metrics</h4>
              <ul style={{ marginTop: 0, paddingLeft: 20 }}>
                {typeof result.metrics.linesOfCode === 'number' && (
                  <li>Lines of code: {result.metrics.linesOfCode}</li>
                )}
                {result.metrics.language && <li>Language: {result.metrics.language}</li>}
                {result.metrics.version && <li>Version: {result.metrics.version}</li>}
              </ul>
            </>
          )}
        </div>
      ) : (
        <div className="error-message" style={{ marginTop: 16 }}>
          No analysis data found. Please run analysis again from the dashboard.
        </div>
      )}
    </div>
  );
};

export default AnalysisResultPage;




