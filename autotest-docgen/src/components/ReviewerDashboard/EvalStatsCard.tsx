import React from 'react';
import { type EvalStatsData } from './types';

const EvalStatsCard: React.FC<{ evalData: EvalStatsData; isDark?: boolean }> = ({ evalData, isDark = false }) => {
  const colors: Record<string, string> = { EXCELLENT: '#10b981', GOOD: '#3b82f6', ACCEPTABLE: '#f59e0b', POOR: '#ef4444' };
  const rawScore = evalData.average_score;
  const score100 = rawScore > 1 ? rawScore : rawScore * 100;
  const scoreColor = score100 >= 70 ? '#10b981' : score100 >= 50 ? '#f59e0b' : '#ef4444';
  return (
    <div className="rd-chart rd-anim-scalein">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </div>
        <div>
          <h3 className={`font-semibold text-sm ${isDark ? 'text-gray-100' : 'text-gray-800'}`}>Evaluation Quality</h3>
          <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{evalData.total_evaluations} total evaluations</p>
        </div>
      </div>
      {/* Score — X.X / 100 */}
      <div className="mb-4">
        <div className="flex items-baseline gap-1 mb-1">
          <span style={{ fontSize: '36px', fontWeight: '800', color: scoreColor, lineHeight: 1 }}>{score100.toFixed(1)}</span>
          <span style={{ fontSize: '16px', fontWeight: '600', color: isDark ? '#6b7280' : '#9ca3af' }}>/ 100</span>
        </div>
        <p style={{ fontSize: '12px', color: isDark ? '#6b7280' : '#9ca3af' }}>Average evaluation score</p>
      </div>
      {/* Verdict stacked bar */}
      <div style={{ height: '10px', backgroundColor: isDark ? '#374151' : '#f3f4f6', borderRadius: '6px', overflow: 'hidden', marginBottom: '10px' }}>
        <div className="flex h-full">
          {evalData.verdict_distribution.map((v, i) => {
            const pct = evalData.total_evaluations > 0 ? (v.count / evalData.total_evaluations) * 100 : 0;
            return <div key={v._id} style={{ width: `${pct}%`, backgroundColor: colors[v._id] || '#8b5cf6', transition: 'width .6s ease', animation: `stackBar .8s ease-out ${i * .08}s both` }} />;
          })}
        </div>
      </div>
      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {evalData.verdict_distribution.map(v => (
          <div key={v._id} className="flex items-center gap-1.5">
            <div style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: colors[v._id] || '#8b5cf6', flexShrink: 0 }} />
            <span style={{ fontSize: '11px', color: isDark ? '#9ca3af' : '#6b7280' }}>{v._id}</span>
            <span style={{ fontSize: '11px', fontWeight: '700', color: isDark ? '#f3f4f6' : '#111827' }}>{v.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EvalStatsCard;
