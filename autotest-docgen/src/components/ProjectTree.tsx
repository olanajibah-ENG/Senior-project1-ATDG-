import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronDown, ChevronRight,
  Folder, FolderOpen, AlertCircle, Loader, RefreshCw
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface FileNode {
  id?: string;
  name: string;
  type: 'file' | 'folder';
  filepath?: string;
  file_type?: string;
  version_number?: number;
  /** API statuses: 'modified' | 'added' | 'none' | legacy: 'new_or_modified' | 'unchanged' | 'new' */
  status?: string;
  language?: string;
  children?: FileNode[];
  /** Analysis result attached to this file node, if available */
  analysis_result?: { id: string };
}

interface ProjectTreeProps {
  projectId: string;
  selectedNodeId: string | null;
  onSelectFile: (node: FileNode) => void;
  isDarkMode: boolean;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getFileExtension(name: string): string {
  return name.split('.').pop()?.toLowerCase() || '';
}

function getAuthToken(): string {
  return localStorage.getItem('access_token') || '';
}

function buildTree(files: any[]): FileNode[] {
  const root: FileNode[] = [];
  files.forEach(file => {
    const path = (file.filepath || file.filename || file.name || '').replace(/^\//, '');
    const parts = path.split('/');
    let current = root;
    parts.forEach((part: string, index: number) => {
      const isLast = index === parts.length - 1;
      let node = current.find(n => n.name === part);
      if (!node) {
        node = {
          name: part,
          type: isLast ? 'file' : 'folder',
          filepath: path,
          id: isLast ? (file.file_id || file.id || file._id || undefined) : undefined,
          file_type: isLast ? (file.file_type || getFileExtension(part)) : undefined,
          version_number: isLast ? (file.version ?? file.version_number) : undefined,
          // Normalise both old and new API status shapes
          status: isLast ? (file.status || 'none') : undefined,
          language: isLast ? file.language : undefined,
          // Attach analysis_result if the API already returned it on the file object
          analysis_result: isLast && file.analysis_result?.id
            ? { id: file.analysis_result.id }
            : undefined,
          children: isLast ? undefined : [],
        };
        current.push(node);
      }
      if (!isLast && node.children) current = node.children;
    });
  });
  return root;
}

/**
 * Walk a tree and attach analysis_result to file nodes whose id matches
 * a code_file_id in the provided analysis results map.
 */
function attachAnalysisResults(
  nodes: FileNode[],
  analysisMap: Record<string, string>  // code_file_id → analysis result id
): void {
  nodes.forEach(node => {
    if (node.type === 'file' && node.id && analysisMap[node.id]) {
      node.analysis_result = { id: analysisMap[node.id] };
    }
    if (node.children) attachAnalysisResults(node.children, analysisMap);
  });
}

function countFiles(nodes: FileNode[]): number {
  return nodes.reduce((acc, n) =>
    acc + (n.type === 'file' ? 1 : countFiles(n.children || [])), 0);
}

// ─── File Icon ────────────────────────────────────────────────────────────────

// ─── File Icon — unique icon per extension ───────────────────────────────────

const FileIcon: React.FC<{ name: string; size?: number }> = ({ name, size = 16 }) => {
  const ext = getFileExtension(name);
  const s = size;

  // ── Language-specific SVG icons ──────────────────────────────────
  if (ext === 'py') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#3b82f6" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#3b82f6" fontFamily="monospace">Py</text>
    </svg>
  );
  if (ext === 'js' || ext === 'jsx') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#f59e0b" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#f59e0b" fontFamily="monospace">JS</text>
    </svg>
  );
  if (ext === 'ts' || ext === 'tsx') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#60a5fa" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#60a5fa" fontFamily="monospace">TS</text>
    </svg>
  );
  if (ext === 'java') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#f97316" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#f97316" fontFamily="monospace">JAV</text>
    </svg>
  );
  if (ext === 'kt') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#a855f7" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#a855f7" fontFamily="monospace">KT</text>
    </svg>
  );
  if (ext === 'go') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#06b6d4" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#06b6d4" fontFamily="monospace">Go</text>
    </svg>
  );
  if (ext === 'rs') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#f472b6" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#f472b6" fontFamily="monospace">RS</text>
    </svg>
  );
  if (ext === 'rb') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#ef4444" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#ef4444" fontFamily="monospace">RB</text>
    </svg>
  );
  if (ext === 'php') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#a78bfa" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#a78bfa" fontFamily="monospace">PHP</text>
    </svg>
  );
  if (ext === 'cs') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#8b5cf6" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#8b5cf6" fontFamily="monospace">C#</text>
    </svg>
  );
  if (ext === 'cpp' || ext === 'c' || ext === 'h') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#64748b" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="700" fill="#64748b" fontFamily="monospace">C++</text>
    </svg>
  );
  if (ext === 'swift') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#f97316" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7" fontWeight="700" fill="#f97316" fontFamily="monospace">SWF</text>
    </svg>
  );
  if (ext === 'dart') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#06b6d4" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#06b6d4" fontFamily="monospace">DRT</text>
    </svg>
  );
  if (ext === 'scala') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#ef4444" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#ef4444" fontFamily="monospace">SCL</text>
    </svg>
  );
  if (ext === 'r') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#3b82f6" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="10" fontWeight="700" fill="#3b82f6" fontFamily="monospace">R</text>
    </svg>
  );

  // ── Config / Data ─────────────────────────────────────────────────
  if (ext === 'json') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#f472b6" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7" fontWeight="700" fill="#f472b6" fontFamily="monospace">{'{}'}</text>
    </svg>
  );
  if (ext === 'yaml' || ext === 'yml') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#fb923c" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7" fontWeight="700" fill="#fb923c" fontFamily="monospace">YML</text>
    </svg>
  );
  if (ext === 'toml') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#fb923c" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7" fontWeight="700" fill="#fb923c" fontFamily="monospace">TML</text>
    </svg>
  );
  if (ext === 'xml') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#fb923c" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#fb923c" fontFamily="monospace">XML</text>
    </svg>
  );
  if (ext === 'env') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#10b981" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7" fontWeight="700" fill="#10b981" fontFamily="monospace">ENV</text>
    </svg>
  );

  // ── Web ───────────────────────────────────────────────────────────
  if (ext === 'html' || ext === 'htm') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#fb923c" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7" fontWeight="700" fill="#fb923c" fontFamily="monospace">HTM</text>
    </svg>
  );
  if (ext === 'css') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#34d399" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#34d399" fontFamily="monospace">CSS</text>
    </svg>
  );
  if (ext === 'scss' || ext === 'less') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#f472b6" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#f472b6" fontFamily="monospace">SCSS</text>
    </svg>
  );

  // ── Docs ──────────────────────────────────────────────────────────
  if (ext === 'md') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#60a5fa" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#60a5fa" fontFamily="monospace">MD</text>
    </svg>
  );
  if (ext === 'pdf') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#ef4444" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#ef4444" fontFamily="monospace">PDF</text>
    </svg>
  );
  if (ext === 'txt' || ext === 'rst') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#94a3b8" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#94a3b8" fontFamily="monospace">TXT</text>
    </svg>
  );

  // ── Images ────────────────────────────────────────────────────────
  if (['png','jpg','jpeg','gif','webp','ico'].includes(ext)) return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#a78bfa" opacity=".15"/>
      <rect x="2" y="4" width="12" height="8" rx="1.5" stroke="#a78bfa" strokeWidth="1.2"/>
      <circle cx="5.5" cy="7" r="1" fill="#a78bfa"/>
      <path d="M2 11l3-3 2.5 2.5L10 8l4 4" stroke="#a78bfa" strokeWidth="1" strokeLinejoin="round"/>
    </svg>
  );
  if (ext === 'svg') return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#a78bfa" opacity=".15"/>
      <text x="8" y="12" textAnchor="middle" fontSize="8" fontWeight="700" fill="#a78bfa" fontFamily="monospace">SVG</text>
    </svg>
  );

  // ── Default ───────────────────────────────────────────────────────
  const label = ext ? ext.slice(0, 3).toUpperCase() : 'FILE';
  return (
    <svg width={s} height={s} viewBox="0 0 16 16" fill="none">
      <rect width="16" height="16" rx="3" fill="#667eea" opacity=".12"/>
      <text x="8" y="12" textAnchor="middle" fontSize={label.length > 2 ? '6.5' : '8'} fontWeight="700" fill="#667eea" fontFamily="monospace">{label}</text>
    </svg>
  );
};

// ─── Status badge helper ──────────────────────────────────────────────────────

/** Returns 'M' (modified), 'U' (added/new), or null (unchanged/none) */
function getStatusBadge(status?: string): 'M' | 'U' | null {
  if (!status) return null;
  const s = status.toLowerCase();
  if (s === 'modified' || s === 'new_or_modified') return 'M';
  if (s === 'added' || s === 'new') return 'U';
  return null;
}

// ─── Tree Node ────────────────────────────────────────────────────────────────

const TreeNode: React.FC<{
  node: FileNode;
  depth: number;
  selectedId: string | null;
  onSelect: (node: FileNode) => void;
  isDarkMode: boolean;
}> = ({ node, depth, selectedId, onSelect, isDarkMode }) => {
  const [open, setOpen] = useState(depth === 0);

  if (node.type === 'folder') {
    return (
      <div className="pt-folder">
        <button
          className="pt-folder-btn"
          style={{ paddingLeft: `${12 + depth * 16}px` }}
          onClick={() => setOpen(o => !o)}
        >
          <span className="pt-chevron">
            {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </span>
          <span className="pt-folder-icon">
            {open ? <FolderOpen size={16} strokeWidth={1.8} /> : <Folder size={16} strokeWidth={1.8} />}
          </span>
          <span className="pt-node-name">{node.name}</span>
          {node.children && (
            <span className="pt-count">{countFiles(node.children)}</span>
          )}
        </button>
        {open && node.children && (
          <div className="pt-children">
            {node.children.map((child, i) => (
              <TreeNode key={i} node={child} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} isDarkMode={isDarkMode} />
            ))}
          </div>
        )}
      </div>
    );
  }

  const isSelected = node.id === selectedId || node.filepath === selectedId;
  const badge = getStatusBadge(node.status);

  return (
    <button
      className={`pt-file-btn${isSelected ? ' selected' : ''}`}
      style={{ paddingLeft: `${12 + depth * 16}px` }}
      onClick={() => onSelect(node)}
    >
      <span className="pt-file-icon"><FileIcon name={node.name} /></span>
      <span className="pt-node-name">{node.name}</span>

      {/* Status badge — M or U */}
      {badge && (
        <span
          className={`pt-status-badge pt-status-${badge === 'M' ? 'modified' : 'added'}${isDarkMode ? ' dark' : ''}`}
        >
          {badge}
        </span>
      )}

      {/* Version chip */}
      {node.version_number !== undefined && (
        <span className="pt-version">v{node.version_number}</span>
      )}
    </button>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

interface VersionInfo {
  version_number: number;
  created_at: string;
}

const ProjectTree: React.FC<ProjectTreeProps> = ({ projectId, selectedNodeId, onSelectFile, isDarkMode }) => {
  const [tree, setTree] = useState<FileNode[]>([]);
  const [versions, setVersions] = useState<VersionInfo[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load available versions from API
  const loadVersions = useCallback(async () => {
    if (!projectId) return;
    try {
      const token = getAuthToken();
      const res = await fetch(`/api/upm/projects/${projectId}/versions/`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) return;
      const data = await res.json();
      const vList: VersionInfo[] = Array.isArray(data)
        ? data.map((v: any) => ({ version_number: v.version_number, created_at: v.created_at || '' }))
        : (data.versions || []).map((v: any) => ({ version_number: v.version_number, created_at: v.created_at || '' }));
      setVersions(vList);
    } catch (_) {
      // versions are optional — silently ignore
    }
  }, [projectId]);

  const loadFiles = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    setTree([]);

    try {
      const token = getAuthToken();
      const versionParam = selectedVersion ? `?version=${selectedVersion}` : '';
      const url = `/api/upm/projects/${projectId}/tree/${versionParam}`;

      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();

      const files: any[] = data.flat_files || data.files || data.results || [];
      const builtTree = buildTree(files);

      // Fetch analysis results and attach them to matching file nodes.
      // This is what makes selectedNode.analysis_result.id available in FileViewer.
      try {
        const arRes = await fetch('/api/analysis/analysis-results/', {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          credentials: 'include',
        });
        if (arRes.ok) {
          const arData = await arRes.json();
          const results: any[] = Array.isArray(arData)
            ? arData
            : (arData.results || []);
          // Build a map: code_file_id → analysis result id
          const analysisMap: Record<string, string> = {};
          results.forEach((r: any) => {
            const fileId = r.code_file_id || r.file_id;
            if (fileId && r.id) analysisMap[fileId] = r.id;
          });
          attachAnalysisResults(builtTree, analysisMap);
        }
      } catch (_) {
        // Non-critical — tree still renders, Generate Logic will fall back to its own lookup
      }

      setTree(builtTree);
    } catch (err: any) {
      setError(err.message || 'Failed to load project files');
    } finally {
      setLoading(false);
    }
  }, [projectId, selectedVersion]);

  useEffect(() => { loadVersions(); }, [loadVersions]);
  useEffect(() => { loadFiles(); }, [loadFiles]);

  const formatVersionDate = (dateStr: string) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    return ` (${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()})`;
  };

  return (
    <div className={`pt-tree-panel${isDarkMode ? ' dark' : ' light'}`}>
      {/* Panel header */}
      <div className="pt-panel-header">
        <span className="pt-panel-title">
          <Folder size={15} />
          Files
          {tree.length > 0 && <span className="pt-panel-count">{countFiles(tree)}</span>}
        </span>

        <div className="pt-panel-controls">
          {/* Version selector */}
          <div className="pt-version-wrap">
            <label htmlFor="pt-ver-sel">Version:</label>
            <select
              id="pt-ver-sel"
              className="pt-version-sel"
              value={selectedVersion}
              onChange={e => setSelectedVersion(e.target.value)}
            >
              <option value="">Latest Version</option>
              {versions.map(v => (
                <option key={v.version_number} value={String(v.version_number)}>
                  Version {v.version_number}{formatVersionDate(v.created_at)}
                </option>
              ))}
            </select>
          </div>

          <button className="pt-refresh-btn" onClick={loadFiles} title="Refresh">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Tree scroll area */}
      <div className="pt-scroll">
        {loading && (
          <div className="pt-center">
            <Loader size={20} className="pt-spin" />
            <span>Loading files…</span>
          </div>
        )}

        {!loading && error && (
          <div className="pt-center pt-error">
            <AlertCircle size={20} />
            <span>{error}</span>
            <button className="pt-retry-btn" onClick={loadFiles}>Retry</button>
          </div>
        )}

        {!loading && !error && tree.length === 0 && (
          <div className="pt-center pt-muted">
            <FolderOpen size={32} strokeWidth={1} />
            <span>No files found</span>
            <span className="pt-hint">Upload a ZIP to this project first</span>
          </div>
        )}

        {!loading && !error && tree.length > 0 && (
          <div className="pt-tree-root">
            {tree.map((node, i) => (
              <TreeNode
                key={i}
                node={node}
                depth={0}
                selectedId={selectedNodeId}
                onSelect={onSelectFile}
                isDarkMode={isDarkMode}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectTree;
