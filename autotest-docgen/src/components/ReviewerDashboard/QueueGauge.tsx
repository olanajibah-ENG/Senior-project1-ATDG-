import React from 'react';
import { type StatsData } from './types';

const QueueGauge: React.FC<{ data: StatsData }> = ({ data }) => {
  const val = data.avg_queue_time_ms ?? 0, MAX = 2000, pct = Math.min(val / MAX, 1);
  const cx = 140, cy = 108, r = 82, toRad = (d: number) => d * Math.PI / 180;
  const bgX1 = cx - r, bgY1 = cy, bgX2 = cx + r;
  const valDeg = 180 - pct * 180, valRad = toRad(valDeg);
  const valX = cx + r * Math.cos(valRad), valY = cy - r * Math.sin(valRad), largeArc = pct > .5 ? 1 : 0;
  const color = pct < .25 ? '#10b981' : pct < .6 ? '#f59e0b' : '#ef4444';
  const nRad = toRad(180 - pct * 180), nX = cx + 68 * Math.cos(nRad), nY = cy - 68 * Math.sin(nRad);
  const [sLabel, sBg, sTxt] = val === 0 ? ['No queue', '#ecfdf5', '#065f46'] : val < 500 ? ['Fast', '#ecfdf5', '#065f46'] : val < 2000 ? ['Moderate', '#fffbeb', '#92400e'] : ['Slow', '#fef2f2', '#991b1b'];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg viewBox="0 0 280 130" width="280" height="130" style={{ display: 'block', overflow: 'visible' }}>
        <path d={`M ${bgX1} ${bgY1} A ${r} ${r} 0 0 1 ${bgX2} ${bgY1}`} fill="none" stroke="#e2e8f0" strokeWidth="14" strokeLinecap="round" />
        {pct > 0 && <path d={`M ${bgX1} ${bgY1} A ${r} ${r} 0 ${largeArc} 1 ${valX} ${valY}`} fill="none" stroke={color} strokeWidth="14" strokeLinecap="round" />}
        {[{ deg: 172, label: '0', c: '#10b981' }, { deg: 90, label: '500ms', c: '#f59e0b' }, { deg: 8, label: '2s', c: '#ef4444' }].map(({ deg, label, c }) => {
          const rad = toRad(deg), tx = cx + (r + 18) * Math.cos(rad), ty = cy - (r + 18) * Math.sin(rad);
          return <text key={deg} x={tx} y={ty} textAnchor="middle" fill={c} fontSize="9" fontFamily="system-ui">{label}</text>;
        })}
        <line x1={cx} y1={cy} x2={nX} y2={nY} stroke="#334155" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="6" fill="#334155" /><circle cx={cx} cy={cy} r="3" fill="white" />
        <text x={cx} y={cy + 20} textAnchor="middle" fill={color} fontSize="22" fontWeight="700" fontFamily="system-ui">{val}</text>
        <text x={cx} y={cy + 34} textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="system-ui">milliseconds</text>
        <text x={cx - r - 4} y={cy + 16} textAnchor="end" fill="#94a3b8" fontSize="9" fontFamily="system-ui">Fast</text>
        <text x={cx + r + 4} y={cy + 16} textAnchor="start" fill="#94a3b8" fontSize="9" fontFamily="system-ui">Slow</text>
      </svg>
      <span style={{ marginTop: '8px', fontSize: '12px', fontWeight: 600, padding: '4px 14px', borderRadius: '9999px', background: sBg, color: sTxt }}>{sLabel}</span>
    </div>
  );
};

export default QueueGauge;
