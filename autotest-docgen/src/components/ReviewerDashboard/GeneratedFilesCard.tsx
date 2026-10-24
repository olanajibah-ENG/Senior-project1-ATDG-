import React from 'react';

const GeneratedFilesCard: React.FC<{ files: Record<string, { count: number; avg_size_bytes: number; max_size_bytes: number; total_downloads: number }>; isDark?: boolean }> = ({ files, isDark = false }) => {
  const types = Object.entries(files);
  const totF = types.reduce((s, [_, d]) => s + d.count, 0);
  const totD = types.reduce((s, [_, d]) => s + d.total_downloads, 0);
  const icons: Record<string, string> = { markdown: '📄', pdf: '📕' };
  return (
    <div className="rd-chart rd-anim-fadeup-1">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
          </svg>
        </div>
        <div><h3 className={`font-semibold text-sm ${isDark ? 'text-gray-100' : 'text-gray-800'}`}>Generated Files</h3><p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{totF} files · {totD} downloads</p></div>
      </div>
      {types.length === 0
        ? <div className="text-center text-gray-400 py-8 text-sm">No files generated yet</div>
        : <div className="space-y-3">
          {types.map(([type, d], idx) => (
            <div key={type} className="rd-file-item" style={{ background: 'var(--rd-file-item-bg)', animation: `scaleIn .4s ease-out ${idx * .1}s both` }}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span style={{ fontSize: '18px' }}>{icons[type] || '📄'}</span>
                  <span className="text-xs font-bold text-gray-600 bg-gray-200 px-2 py-1 rounded">{type.toUpperCase()}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                <div><span style={{ color: '#3b82f6', fontWeight: '700' }}>{d.count}</span><span style={{ color: '#6b7280' }}> Files</span></div>
                <div><span style={{ color: '#6b7280' }}>Avg: {(d.avg_size_bytes / 1024).toFixed(1)}KB</span></div>
                <div><span style={{ color: '#6b7280' }}>Max: {(d.max_size_bytes / 1024).toFixed(1)}KB</span></div>
                <div><span style={{ color: '#10b981', fontWeight: '700' }}>{d.total_downloads}</span><span style={{ color: '#6b7280' }}> Downloads</span></div>
              </div>
              <div style={{ height: '4px', backgroundColor: '#e5e7eb', borderRadius: '2px' }}>
                <div style={{ height: '4px', backgroundColor: '#3b82f6', borderRadius: '2px', width: `${Math.min((d.total_downloads / Math.max(d.count, 1)) * 100, 100)}%`, animation: 'barH .6s ease-out both' }} />
              </div>
            </div>
          ))}
        </div>
      }
    </div>
  );
};

export default GeneratedFilesCard;
