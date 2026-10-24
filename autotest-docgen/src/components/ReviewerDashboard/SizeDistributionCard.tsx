import React from 'react';

const SizeDistributionCard: React.FC<{ dist: { under_50KB: number; '50_to_200KB': number; over_200KB: number }; isDark?: boolean }> = ({ dist, isDark = false }) => {
  const data = [
    { label: '<50KB', value: dist.under_50KB, color: '#10b981' },
    { label: '50-200KB', value: dist['50_to_200KB'], color: '#3b82f6' },
    { label: '>200KB', value: dist.over_200KB, color: '#f59e0b' },
  ];
  const mx = Math.max(...data.map(d => d.value), 1);
  const total = data.reduce((s, d) => s + d.value, 0);
  return (
    <div className="rd-chart rd-anim-fadeup-2">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </div>
        <div><h3 className={`font-semibold text-sm ${isDark ? 'text-gray-100' : 'text-gray-800'}`}>File Size Distribution</h3><p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{total} total files</p></div>
      </div>
      <div className="flex items-end justify-center gap-6" style={{ height: '140px' }}>
        {data.map((item, idx) => {
          // Always render bars — 6px minimum height when value=0
          const h = total === 0 ? 6 : mx > 0 ? Math.max((item.value / mx) * 120, item.value > 0 ? 4 : 6) : 6;
          const isEmpty = item.value === 0;
          return <div key={item.label} className="flex flex-col items-center">
            <div style={{ fontSize: '13px', fontWeight: '700', color: isEmpty ? '#9ca3af' : '#1f2937', marginBottom: '4px' }}>{item.value}</div>
            <div style={{ width: '44px', height: `${h}px`, backgroundColor: item.color, borderRadius: '4px 4px 0 0', transformOrigin: 'bottom', opacity: isEmpty ? 0.25 : 1, animation: `barV .6s cubic-bezier(.34,1.56,.64,1) ${idx * .12}s both`, cursor: 'pointer', transition: 'opacity .2s' }}
              onMouseEnter={e => (e.currentTarget.style.opacity = isEmpty ? '0.4' : '0.75')} onMouseLeave={e => (e.currentTarget.style.opacity = isEmpty ? '0.25' : '1')} />
            <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '6px', textAlign: 'center' }}>{item.label}</div>
          </div>;
        })}
      </div>
      {total === 0 && <div style={{ textAlign: 'center', fontSize: '11px', color: '#9ca3af', marginTop: '8px' }}>No files analyzed yet</div>}
    </div>
  );
};

export default SizeDistributionCard;
