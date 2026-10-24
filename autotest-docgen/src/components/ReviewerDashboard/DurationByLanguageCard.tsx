import React from 'react';

const DurationByLanguageCard: React.FC<{ data: Record<string, { avg_duration_ms: number; count: number }>; isDark?: boolean }> = ({ data, isDark = false }) => {
  const langs = Object.entries(data);
  const maxMs = Math.max(...langs.map(([_, d]) => d.avg_duration_ms), 1);
  const colors: Record<string, string> = { python: '#3b82f6', java: '#f59e0b', javascript: '#10b981', csharp: '#8b5cf6' };
  return (
    <div className="rd-chart rd-anim-fadeup">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#14b8a6' }}>&lt;/&gt;</span>
        </div>
        <div><h3 className={`font-semibold text-sm ${isDark ? 'text-gray-100' : 'text-gray-800'}`}>Duration by Language</h3><p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Avg processing time per language</p></div>
      </div>
      {langs.length === 0
        ? <div className="text-center text-gray-400 py-8 text-sm">No language data available</div>
        : <div className="space-y-4">
          {langs.map(([lang, stats], idx) => {
            const color = colors[lang] || '#6366f1';
            const isZero = stats.avg_duration_ms === 0;
            const w = isZero ? 5 : (stats.avg_duration_ms / maxMs) * 100;
            return <div key={lang}>
              <div className="flex items-center gap-3 mb-1">
                <div style={{ width: '90px', fontSize: '13px', color: '#374151', fontWeight: '500', textTransform: 'capitalize' }}>{lang}</div>
                <div className="flex-1 relative" style={{ height: '10px' }}>
                  <div style={{ height: '10px', backgroundColor: '#f3f4f6', borderRadius: '9999px', position: 'absolute', inset: 0 }} />
                  <div style={{ position: 'absolute', top: 0, left: 0, height: '10px', backgroundColor: color, borderRadius: '9999px', width: `${w}%`, opacity: isZero ? 0.35 : 1, animation: `barH .8s cubic-bezier(.34,1.56,.64,1) ${idx * .1}s both` }} />
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280', minWidth: '70px', textAlign: 'right' }}>{stats.avg_duration_ms}ms · {stats.count} files</div>
              </div>
            </div>;
          })}
        </div>
      }
    </div>
  );
};

export default DurationByLanguageCard;
