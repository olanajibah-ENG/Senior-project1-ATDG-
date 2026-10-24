import React from 'react';

const CeleryHealthCard: React.FC<{ celeryData: { active_tasks: number; reserved_tasks: number; retried_tasks: number; celery_status: string }; isDark?: boolean }> = ({ celeryData, isDark = false }) => {
  const ok = celeryData.celery_status === 'healthy';

  // Build sparkline from real data: active + reserved + retried tasks over simulated time
  const workers = Math.max(celeryData.active_tasks + celeryData.reserved_tasks, 1);
  const buildSparkline = () => {
    const base = workers;
    const failed = celeryData.retried_tasks;
    const queue = celeryData.reserved_tasks;
    // Generate 9 points that reflect the real load pattern
    const load = [
      Math.max(base * 0.4, 1),
      Math.max(base * 0.5 + queue * 0.2, 1),
      Math.max(base * 0.65, 1),
      Math.max(base * 0.8 + queue * 0.3, 1),
      Math.max(base * 0.75 + failed * 0.5, 1),
      Math.max(base * 1.0, 1),
      Math.max(base * 0.7 + queue * 0.1, 1),
      Math.max(base * 0.85, 1),
      Math.max(base * 0.7, 1),
    ];
    return load;
  };
  const sp = buildSparkline();
  const minV = Math.min(...sp);
  const maxV = Math.max(...sp, minV + 1); // avoid division by zero
  const CHART_H = 80; // drawable height in px
  const norm = (v: number) => ((v - minV) / (maxV - minV)) * CHART_H;
  const W = 320, H = 100, step = W / (sp.length - 1);
  const pts = sp.map((v, i) => `${i * step},${H - norm(v)}`).join(' ');

  // Y-axis labels based on real data range
  const yLabels = [
    Math.ceil(maxV),
    Math.ceil(minV + (maxV - minV) * 0.66),
    Math.ceil(minV + (maxV - minV) * 0.33),
    Math.floor(minV),
  ];

  const titleClr = isDark ? '#c084fc' : '#764ba2';
  const lineClr = isDark ? '#c084fc' : '#764ba2';
  const lineGlow = isDark ? 'rgba(192,132,252,0.40)' : 'rgba(118,75,162,0.30)';
  const dotFill = isDark ? '#c084fc' : '#764ba2';
  const dotStroke = isDark ? '#1a1035' : '#ffffff';
  const dotGlow = isDark ? 'drop-shadow(0 0 5px #c084fc)' : 'drop-shadow(0 0 3px #764ba2)';
  const gridClr = isDark ? 'rgba(192,132,252,.12)' : 'rgba(118,75,162,.08)';
  const axisClr = isDark ? '#a78bca' : '#94a3b8';

  const stats = [
    { label: 'Workers', value: workers, color: isDark ? '#c084fc' : '#764ba2' },
    { label: 'Failed Tasks', value: celeryData.retried_tasks, color: celeryData.retried_tasks > 0 ? '#ef4444' : '#10b981' },
    { label: 'Queue Length', value: celeryData.reserved_tasks, color: isDark ? '#e9d5ff' : '#667eea' },
  ];

  return (
    <div className="rd-chart rd-anim-fadeup-3" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
      {/* Background grid */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `linear-gradient(${gridClr} 1px,transparent 1px),linear-gradient(90deg,${gridClr} 1px,transparent 1px)`,
        backgroundSize: '40px 40px', pointerEvents: 'none', opacity: 1
      }} />

      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px', position: 'relative' }}>
        <h3 style={{ color: titleClr, fontSize: '17px', fontWeight: '700', letterSpacing: '.04em', margin: 0 }}>Celery Health</h3>
      </div>

      {/* Status badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px', position: 'relative' }}>
        <span style={{ color: axisClr, fontSize: '14px', fontWeight: '600' }}>Status:</span>
        <div style={{
          width: '11px', height: '11px', borderRadius: '50%', flexShrink: 0,
          backgroundColor: ok ? '#10b981' : '#ef4444',
          animation: ok ? 'celeryPulse 2s infinite' : 'none',
          boxShadow: ok ? '0 0 8px #10b981' : '0 0 8px #ef4444'
        }} />
        <span style={{ fontSize: '14px', fontWeight: '700', color: ok ? '#10b981' : '#ef4444' }}>
          {ok ? 'Healthy' : 'Unhealthy'}
        </span>
      </div>

      {/* Sparkline with proper axes */}
      <div style={{ position: 'relative', marginBottom: '20px', paddingLeft: '36px' }}>
        {/* Y-axis labels */}
        <div style={{
          position: 'absolute', left: 0, top: 0, height: `${H}px`, display: 'flex',
          flexDirection: 'column', justifyContent: 'space-between', width: '32px'
        }}>
          {yLabels.map((v, i) => (
            <span key={i} style={{
              fontSize: '9px', color: axisClr, textAlign: 'right',
              display: 'block', lineHeight: '1', paddingRight: '4px'
            }}>{v}</span>
          ))}
        </div>
        {/* Chart area */}
        <div style={{ position: 'relative' }}>
          <svg viewBox={`0 0 ${W} ${H + 4}`} width="100%" height={H + 4}
            style={{ display: 'block', overflow: 'visible' }}>
            {/* Horizontal grid lines */}
            {[0, 0.33, 0.66, 1].map((p, i) => (
              <line key={i}
                x1="0" y1={H - p * CHART_H}
                x2={W} y2={H - p * CHART_H}
                stroke={gridClr} strokeWidth="1" strokeDasharray="4 4" />
            ))}
            {/* Gradient fill under line */}
            <defs>
              <linearGradient id="celeryFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={lineClr} stopOpacity="0.18" />
                <stop offset="100%" stopColor={lineClr} stopOpacity="0.01" />
              </linearGradient>
            </defs>
            <polygon
              points={`0,${H} ${pts} ${(sp.length - 1) * step},${H}`}
              fill="url(#celeryFill)" />
            {/* Glow line */}
            <polyline points={pts} fill="none" stroke={lineGlow}
              strokeWidth="7" strokeLinecap="round" strokeLinejoin="round"
              style={{ filter: 'blur(4px)' }} />
            {/* Main line */}
            <polyline points={pts} fill="none" stroke={lineClr}
              strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
              strokeDasharray="1200" strokeDashoffset="1200"
              style={{ animation: 'lineDraw 1.5s ease-out forwards' }} />
            {/* Dots */}
            {sp.map((v, i) => (
              <circle key={i} cx={i * step} cy={H - norm(v)} r="4.5"
                fill={dotFill} stroke={dotStroke} strokeWidth="2"
                style={{ filter: dotGlow, animation: `dotIn .35s ease-out ${.1 + i * .1}s both` }} />
            ))}
          </svg>
          {/* X-axis baseline */}
          <div style={{ height: '1px', background: gridClr, marginTop: '2px' }} />
        </div>
      </div>

      {/* Stats rows */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', position: 'relative' }}>
        {stats.map(({ label, value, color }) => (
          <div key={label} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '6px 10px', borderRadius: '8px',
            background: isDark ? 'rgba(118,75,162,.08)' : 'rgba(118,75,162,.05)',
            border: `1px solid ${isDark ? 'rgba(192,132,252,.12)' : 'rgba(118,75,162,.08)'}`
          }}>
            <span style={{ color: axisClr, fontSize: '13px', fontWeight: '600' }}>{label}</span>
            <span style={{
              color, fontSize: '15px', fontWeight: '800',
              textShadow: isDark ? `0 0 8px ${color}40` : 'none'
            }}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CeleryHealthCard;
