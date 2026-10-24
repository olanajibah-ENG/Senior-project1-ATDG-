import React from 'react';
import { type StatsData } from './types';

const ThroughputChart: React.FC<{ data: StatsData }> = ({ data }) => {
  const t = data.throughput_24h ?? 0;
  const allZero = t === 0;
  const hourly = Array.from({ length: 24 }, (_, i) => allZero ? 0 : Math.max(0, Math.floor(t * Math.sin(i / 3 + 1) * .35 + t * .12)));
  const mx = Math.max(...hourly, 1);
  return (
    <div>
      <div style={{ display: 'flex', gap: '8px', height: '160px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '28px', paddingRight: '4px', paddingBottom: '20px' }}>
          {[mx, Math.floor(mx / 2), 0].map((v, i) => <span key={i} style={{ fontSize: '10px', color: '#94a3b8', textAlign: 'right', display: 'block' }}>{v}</span>)}
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, position: 'relative', borderLeft: '1.5px solid #94a3b8', borderBottom: '1.5px solid #94a3b8' }}>
            {[25, 50, 75].map(p => <div key={p} style={{ position: 'absolute', left: 0, right: 0, top: `${p}%`, height: '1px', borderTop: '1px dashed #e2e8f0' }} />)}
            <div style={{ display: 'flex', alignItems: 'flex-end', height: '100%', padding: '4px 4px 0', gap: '2px' }}>
              {hourly.map((v, idx) => {
                const pct = allZero ? 3 : Math.max(3, (v / mx) * 100);
                return <div key={idx} style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
                  <div style={{ width: '100%', height: `${pct}%`, background: allZero ? '#cbd5e1' : 'linear-gradient(to bottom,#3b82f6,#6366f1)', borderRadius: '2px 2px 0 0', opacity: allZero ? .5 : 1 }} />
                </div>;
              })}
            </div>
            {allZero && <div style={{ position: 'absolute', bottom: '4px', left: 0, right: 0, display: 'flex', justifyContent: 'center', pointerEvents: 'none' }}><span style={{ fontSize: '10px', color: '#cbd5e1', background: 'white', padding: '0 4px' }}>0 jobs in last 24h</span></div>}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '4px', paddingLeft: '4px' }}>
            {[0, 6, 12, 18, 23].map(h => <span key={h} style={{ fontSize: '10px', color: '#94a3b8' }}>{String(h).padStart(2, '0')}:00</span>)}
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: 'linear-gradient(#3b82f6,#6366f1)' }} />
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>Jobs per hour (estimated)</span>
        </div>
        <span style={{ fontSize: '11px', color: '#94a3b8' }}>Last 24h</span>
      </div>
    </div>
  );
};

export default ThroughputChart;
