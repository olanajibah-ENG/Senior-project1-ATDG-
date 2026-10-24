import React from 'react';

const ErrorClassificationCard: React.FC<{ errorData: Record<string, number>; totalFailed: number; isDark?: boolean }> = ({ errorData, totalFailed, isDark = false }) => {
  // Build display categories — always 4 defaults, use real data or 0
  const DEFAULT_CATS = ['Security', 'Logic', 'Style', 'Performance'];
  const colors: Record<string, string> = { Security: '#ef4444', Logic: '#f59e0b', Style: '#667eea', Performance: '#764ba2' };
  const displayCats: [string, number][] = DEFAULT_CATS.map(c => [c, (typeof errorData[c] === 'number') ? errorData[c] : 0]);
  const displayTotal = displayCats.reduce((s, [_, v]) => s + v, 0);
  const allEmpty = displayTotal === 0;
  const circ = 2 * Math.PI * 60;
  let off = 0;

  return (
    <div className="rd-chart">
      <div className="rd-chart-title">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <div>
          <h3>Error Classification</h3>
          <p>Total failed: {String(totalFailed)}</p>
        </div>
      </div>

      {allEmpty && (
        <div className="flex items-center gap-2 mb-3 px-3 py-1 rounded-full"
          style={{ background: 'rgba(16,185,129,.1)', color: '#065f46', width: 'fit-content' }}>
          <svg className="w-4 h-4" style={{ color: '#10b981' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span style={{ fontSize: '12px', fontWeight: 600 }}>No errors — system healthy</span>
        </div>
      )}

      <div className="flex justify-center mb-4">
        <svg width="160" height="160" viewBox="0 0 160 160">
          {/* Background ring */}
          <circle cx="80" cy="80" r="60" fill="none"
            stroke={isDark ? 'rgba(102,126,234,.15)' : 'rgba(102,126,234,.10)'}
            strokeWidth="16" />
          {/* Segments */}
          {displayCats.map(([cat, val], i: number) => {
            const pct = allEmpty ? 0.25 : (val / Math.max(displayTotal, 1));
            const segLen = pct * circ;
            const startOff = off;
            off += segLen;
            return (
              <circle key={cat} cx="80" cy="80" r="60" fill="none"
                stroke={colors[cat] || '#8b5cf6'}
                strokeWidth="16"
                strokeDasharray={`${segLen} ${circ - segLen}`}
                strokeDashoffset={-startOff}
                opacity={allEmpty ? 0.25 : 1}
                style={{
                  transform: 'rotate(-90deg)',
                  transformOrigin: 'center',
                  transition: 'stroke-dasharray .6s ease',
                }} />
            );
          })}
          {/* Center hole */}
          <circle cx="80" cy="80" r="52"
            fill={isDark ? 'rgba(30,41,59,.95)' : 'rgba(255,255,255,.9)'} />
          {/* Center text */}
          <text x="80" y="76" textAnchor="middle"
            fontSize="22" fontWeight="800"
            fill={isDark ? '#f1f5f9' : '#1e293b'}>{String(totalFailed)}</text>
          <text x="80" y="94" textAnchor="middle"
            fontSize="11"
            fill={isDark ? '#94a3b8' : '#64748b'}>errors</text>
        </svg>
      </div>

      {/* Legend — key/value pairs, no [object Object] */}
      <div className="grid grid-cols-2 gap-2">
        {displayCats.map(([cat, val]) => (
          <div key={cat} className="flex items-center gap-2 py-1">
            <div style={{
              width: '10px', height: '10px', borderRadius: '50%',
              backgroundColor: colors[cat] || '#8b5cf6', flexShrink: 0,
              opacity: allEmpty ? 0.3 : 1
            }} />
            <span style={{ fontSize: '12px', color: 'var(--rd-text-secondary)', flex: 1 }}>{String(cat)}</span>
            <span style={{
              fontSize: '12px', fontWeight: '700',
              color: allEmpty ? 'var(--rd-text-secondary)' : 'var(--rd-text-primary)'
            }}>{Number(val)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ErrorClassificationCard;
