import React from 'react';

const VerifierStatsCard: React.FC<{ byType: Record<string, { total: number; verifier_success: number; verifier_fallbacks: number; fallback_rate_percent: number }>; overall: { total_explanations: number; verifier_fallbacks: number; fallback_rate_percent: number }; isDark?: boolean }> = ({ byType, overall, isDark = false }) => {
  const rateBg = (r: number) => r < 20 ? '#ecfdf5' : r <= 50 ? '#fffbeb' : '#fef2f2';
  const rateTxt = (t: string) => t.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  const success = overall.total_explanations - overall.verifier_fallbacks;
  const formatType = (t: string) => t.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  return (
    <div className="rd-chart rd-anim-fadeup-3">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div><h3 className={`font-semibold text-sm ${isDark ? 'text-gray-100' : 'text-gray-800'}`}>Verifier Stats</h3><p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Success and fallback metrics</p></div>
      </div>
      <div className="flex gap-2 mb-4 flex-wrap">
        <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">Total: {overall.total_explanations}</span>
        <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-semibold">Fallbacks: {overall.verifier_fallbacks}</span>
        <span className="px-3 py-1 rounded-full text-xs font-semibold" style={{ backgroundColor: rateBg(overall.fallback_rate_percent), color: rateTxt(overall.fallback_rate_percent.toString()) }}>Rate: {overall.fallback_rate_percent.toFixed(1)}%</span>
      </div>
      <div className="mb-4 overflow-x-auto">
        <table className="w-full text-xs">
          <thead><tr className="text-gray-400 border-b">
            {['Type', 'Total', 'Success', 'Fallbacks', 'Rate'].map(h => <th key={h} className="text-left py-2 pr-4 font-medium">{h}</th>)}
          </tr></thead>
          <tbody>
            {Object.entries(byType).map(([type, s]) => (
              <tr key={type} className="border-b hover:bg-blue-50 transition-colors">
                <td className="py-2 pr-4 font-medium text-gray-700">{type}</td>
                <td className="py-2 pr-4 text-gray-600">{s.total}</td>
                <td className="py-2 pr-4 text-green-600 font-semibold">{s.verifier_success}</td>
                <td className="py-2 pr-4 text-orange-600">{s.verifier_fallbacks}</td>
                <td className="py-2"><span className="px-2 py-1 rounded font-semibold" style={{ backgroundColor: rateBg(s.fallback_rate_percent), color: rateTxt(s.fallback_rate_percent.toString()) }}>{s.fallback_rate_percent.toFixed(1)}%</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ height: '8px', backgroundColor: '#f3f4f6', borderRadius: '4px', overflow: 'hidden' }}>
        <div className="flex h-full">
          <div style={{ width: `${(success / Math.max(overall.total_explanations, 1)) * 100}%`, backgroundColor: '#10b981', animation: 'stackBar .8s ease-out both' }} />
          <div style={{ width: `${(overall.verifier_fallbacks / Math.max(overall.total_explanations, 1)) * 100}%`, backgroundColor: '#f59e0b', animation: 'stackBar .8s ease-out .1s both' }} />
        </div>
      </div>
      <div className="flex gap-4 mt-2 text-xs text-gray-400">
        <span className="flex items-center gap-1"><span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#10b981' }} />Success</span>
        <span className="flex items-center gap-1"><span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#f59e0b' }} />Fallback</span>
      </div>
    </div>
  );
};

export default VerifierStatsCard;
