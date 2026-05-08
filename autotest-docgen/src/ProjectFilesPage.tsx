import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, RefreshCw, Copy, ChevronDown, ChevronRight,
  Folder, FolderOpen, FileText, File, Code, FileJson,
  Image, FileCode, AlertCircle, Loader,
} from 'lucide-react';
import './ProjectFilesPage.css';

interface FileNode {
  id?: string;
  name: string;
  type: 'file' | 'folder';
  filepath?: string;
  file_type?: string;
  version_number?: number;
  children?: FileNode[];
}

interface FileContent {
  content: string;
  filename: string;
  filepath: string;
  file_type: string;
  size?: number;
}

function getFileExtension(name: string): string {
  return name.split('.').pop()?.toLowerCase() ?? '';
}

function formatSize(bytes: number): string {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function getAuthToken(): string {
  return localStorage.getItem('access_token') ?? '';
}

function buildTree(files: any[]): FileNode[] {
  const root: FileNode[] = [];
  for (const file of files) {
    const rawPath: string = (file.filepath || file.filename || file.name || '') as string;
    const path = rawPath.replace(/^\//, '');
    const parts = path.split('/');
    let current = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      let node = current.find(n => n.name === part);
      if (!node) {
        node = {
          name: part,
          type: isLast ? 'file' : 'folder',
          filepath: path,
          id: isLast ? (file.file_id || file.id || file._id || path) : undefined,
          file_type: isLast ? (file.file_type || getFileExtension(part)) : undefined,
          version_number: isLast ? (file.version_number as number | undefined) : undefined,
          children: isLast ? undefined : [],
        };
        current.push(node);
      }
      if (!isLast && node.children) current = node.children;
    }
  }
  return root;
}

function countFiles(nodes: FileNode[]): number {
  return nodes.reduce((acc, n) => acc + (n.type === 'file' ? 1 : countFiles(n.children ?? [])), 0);
}

function highlight(code: string, ext: string): string {
  const esc = (s: string) =>
    s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  let h = esc(code);

  if (['py', 'js', 'ts', 'tsx', 'jsx', 'java', 'go', 'rs', 'rb', 'php', 'cs', 'kt'].includes(ext)) {
    h = h.replace(/(&quot;[^&]*?&quot;|&#39;[^&]*?&#39;|`[^`]*`)/g, '<span class="pf-str">$1</span>');
    h = h.replace(/(\/\/.*$|#.*$)/gm, '<span class="pf-cmt">$1</span>');
    h = h.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="pf-cmt">$1</span>');
    const kw = ext === 'py'
      ? 'def|class|import|from|return|if|elif|else|for|while|with|as|try|except|finally|pass|break|continue|lambda|yield|and|or|not|in|is|None|True|False|async|await'
      : 'import|export|from|const|let|var|function|return|if|else|for|while|class|interface|type|extends|implements|new|this|async|await|try|catch|throw|typeof|instanceof|default|switch|case|break|continue|public|private|protected|static|void|null|undefined|true|false';
    h = h.replace(new RegExp(`\\b(${kw})\\b`, 'g'), '<span class="pf-kw">$1</span>');
    h = h.replace(/\b(\d+\.?\d*)\b/g, '<span class="pf-num">$1</span>');
    h = h.replace(/\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?=\()/g, '<span class="pf-fn">$1</span>');
  } else if (['css', 'scss', 'less'].includes(ext)) {
    h = h.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="pf-cmt">$1</span>');
    h = h.replace(/([.#]?[a-zA-Z_-][a-zA-Z0-9_-]*)\s*\{/g, '<span class="pf-kw">$1</span> {');
    h = h.replace(/([a-z-]+)\s*:/g, '<span class="pf-fn">$1</span>:');
  } else if (ext === 'json') {
    h = h.replace(/(&quot;[^&]*?&quot;)\s*:/g, '<span class="pf-fn">$1</span>:');
    h = h.replace(/:\s*(&quot;[^&]*?&quot;)/g, ': <span class="pf-str">$1</span>');
    h = h.replace(/:\s*(\d+\.?\d*)/g, ': <span class="pf-num">$1</span>');
    h = h.replace(/:\s*(true|false|null)/g, ': <span class="pf-kw">$1</span>');
  } else if (['html', 'xml', 'svg'].includes(ext)) {
    h = h.replace(/(&lt;\/?)([\w-]+)/g, '$1<span class="pf-kw">$2</span>');
    h = h.replace(/([\w-]+)=/g, '<span class="pf-fn">$1</span>=');
    h = h.replace(/(&quot;[^&]*?&quot;)/g, '<span class="pf-str">$1</span>');
  }

  return h;
}

const FileIcon: React.FC<{ name: string; size?: number }> = ({ name, size = 16 }) => {
  const ext = getFileExtension(name);
  const p = { size, strokeWidth: 1.8 };
  if (['py', 'js', 'ts', 'tsx', 'jsx', 'java', 'go', 'rs', 'rb', 'php', 'cs', 'kt', 'cpp', 'c', 'h', 'swift', 'dart', 'r', 'scala'].includes(ext))
    return <FileCode {...p} className="pf-icon-code" />;
  if (['json', 'yaml', 'yml', 'toml', 'xml', 'env'].includes(ext))
    return <FileJson {...p} className="pf-icon-json" />;
  if (['md', 'txt', 'rst', 'pdf', 'doc', 'docx'].includes(ext))
    return <FileText {...p} className="pf-icon-doc" />;
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'webp'].includes(ext))
    return <Image {...p} className="pf-icon-img" />;
  if (['css', 'scss', 'less', 'html', 'htm'].includes(ext))
    return <Code {...p} className="pf-icon-style" />;
  return <File {...p} className="pf-icon-default" />;
};

const TreeNode: React.FC<{
  node: FileNode;
  depth: number;
  selectedId: string | null;
  onSelect: (node: FileNode) => void;
  defaultOpen?: boolean;
}> = ({ node, depth, selectedId, onSelect, defaultOpen = false }) => {
  const [open, setOpen] = useState(defaultOpen || depth === 0);

  if (node.type === 'folder') {
    return (
      <div className="pf-tree-folder">
        <button
          className="pf-tree-folder-btn"
          style={{ paddingLeft: `${12 + depth * 16}px` }}
          onClick={() => setOpen(o => !o)}
        >
          <span className="pf-tree-chevron">
            {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </span>
          <span className="pf-tree-folder-icon">
            {open ? <FolderOpen size={16} strokeWidth={1.8} /> : <Folder size={16} strokeWidth={1.8} />}
          </span>
          <span className="pf-tree-name">{node.name}</span>
          {node.children && <span className="pf-tree-count">{countFiles(node.children)}</span>}
        </button>
        {open && node.children && (
          <div className="pf-tree-children">
            {node.children.map((child, i) => (
              <TreeNode key={i} node={child} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} />
            ))}
          </div>
        )}
      </div>
    );
  }

  const isSelected = node.id === selectedId || node.filepath === selectedId;
  return (
    <button
      className={`pf-tree-file-btn ${isSelected ? 'selected' : ''}`}
      style={{ paddingLeft: `${12 + depth * 16}px` }}
      onClick={() => onSelect(node)}
    >
      <span className="pf-tree-file-icon"><FileIcon name={node.name} /></span>
      <span className="pf-tree-name">{node.name}</span>
      {node.version_number !== undefined && (
        <span className="pf-tree-version">v{node.version_number}</span>
      )}
    </button>
  );
};

const ProjectFilesPage: React.FC = () => {
  const { project_id } = useParams<{ project_id: string }>();
  const navigate = useNavigate();

  const [tree, setTree] = useState<FileNode[]>([]);
  const [allVersions, setAllVersions] = useState<number[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedNode, setSelectedNode] = useState<FileNode | null>(null);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [loadingContent, setLoadingContent] = useState(false);
  const [contentError, setContentError] = useState<string | null>(null);

  const [copied, setCopied] = useState(false);
  const [projectName, setProjectName] = useState('Project');

  const loadFiles = useCallback(async () => {
    if (!project_id) return;
    setLoading(true);
    setError(null);
    setTree([]);
    setSelectedNode(null);
    setFileContent(null);

    try {
      const token = getAuthToken();
      const versionParam = selectedVersion ? `?version=${selectedVersion}` : '';
      const res = await fetch(`/api/upm/projects/${project_id}/folder-upload/${versionParam}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();

      setProjectName(data.project_name || `Project ${project_id}`);
      const files: any[] = data.files || [];
      const versions = [...new Set(files.map((f: any) => f.version_number).filter(Boolean))] as number[];
      versions.sort((a, b) => a - b);
      setAllVersions(versions);
      setTree(buildTree(files));
    } catch (err: any) {
      try {
        const token = getAuthToken();
        const r2 = await fetch(`/api/upm/projects/${project_id}/`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (r2.ok) {
          const p = await r2.json();
          setProjectName(p.title || p.name || `Project ${project_id}`);
        }
      } catch (_) { /* ignore */ }
      setError(err.message || 'Failed to load project files');
    } finally {
      setLoading(false);
    }
  }, [project_id, selectedVersion]);

  useEffect(() => { loadFiles(); }, [loadFiles]);

  const loadFileContent = useCallback(async (node: FileNode) => {
    if (!project_id || !node.id) return;
    setLoadingContent(true);
    setContentError(null);
    setFileContent(null);

    try {
      const token = getAuthToken();
      const res = await fetch(`/api/upm/projects/${project_id}/files/${node.id}/content/`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();

      setFileContent({
        content: data.content || '',
        filename: node.name,
        filepath: node.filepath || node.name,
        file_type: node.file_type || getFileExtension(node.name),
        size: data.size,
      });
    } catch (err: any) {
      setContentError(err.message || 'Failed to load file content');
    } finally {
      setLoadingContent(false);
    }
  }, [project_id]);

  const handleSelectFile = (node: FileNode) => {
    setSelectedNode(node);
    loadFileContent(node);
  };

  const handleCopy = () => {
    if (!fileContent?.content) return;
    navigator.clipboard.writeText(fileContent.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const ext = fileContent ? getFileExtension(fileContent.filename) : '';
  const lines = fileContent?.content.split('\n') || [];

  return (
    <div className="pf-page">
      <div className="pf-topbar">
        <button className="pf-back-btn" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={18} />
          <span>Dashboard</span>
        </button>
        <div className="pf-topbar-center">
          <FolderOpen size={20} className="pf-topbar-icon" />
          <span className="pf-topbar-project">{projectName}</span>
          <span className="pf-topbar-sep">/</span>
          <span className="pf-topbar-label">File Tree</span>
        </div>
        <div className="pf-topbar-right">
          <div className="pf-version-wrap">
            <label htmlFor="pf-ver">Version:</label>
            <select
              id="pf-ver"
              className="pf-version-sel"
              value={selectedVersion}
              onChange={e => setSelectedVersion(e.target.value)}
            >
              <option value="">Latest</option>
              {allVersions.map(v => <option key={v} value={v}>v{v}</option>)}
            </select>
          </div>
          <button className="pf-icon-btn" onClick={loadFiles} title="Refresh">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div className="pf-body">
        <aside className="pf-tree-panel">
          <div className="pf-panel-header">
            <span className="pf-panel-title">
              <Folder size={16} />
              Files
            </span>
            {tree.length > 0 && <span className="pf-panel-count">{countFiles(tree)}</span>}
          </div>
          <div className="pf-tree-scroll">
            {loading && (
              <div className="pf-center">
                <Loader size={22} className="pf-spin" />
                <span>Loading…</span>
              </div>
            )}
            {!loading && error && (
              <div className="pf-center pf-error">
                <AlertCircle size={22} />
                <span>{error}</span>
                <button className="pf-retry-btn" onClick={loadFiles}>Retry</button>
              </div>
            )}
            {!loading && !error && tree.length === 0 && (
              <div className="pf-center pf-muted">
                <FolderOpen size={36} strokeWidth={1} />
                <span>No files found</span>
                <span className="pf-hint">Upload a ZIP to this project first</span>
              </div>
            )}
            {!loading && !error && tree.length > 0 && (
              <div className="pf-tree-root">
                {tree.map((node, i) => (
                  <TreeNode
                    key={i}
                    node={node}
                    depth={0}
                    selectedId={selectedNode?.id || selectedNode?.filepath || null}
                    onSelect={handleSelectFile}
                    defaultOpen
                  />
                ))}
              </div>
            )}
          </div>
        </aside>

        <main className="pf-viewer-panel">
          {!selectedNode && (
            <div className="pf-viewer-empty">
              <FileText size={56} strokeWidth={1} className="pf-muted-icon" />
              <h3>No file selected</h3>
              <p>Click any file in the tree to view its contents</p>
            </div>
          )}
          {selectedNode && (
            <>
              <div className="pf-viewer-header">
                <div className="pf-viewer-title">
                  <FileIcon name={selectedNode.name} size={18} />
                  <span className="pf-viewer-filename">{selectedNode.name}</span>
                  <span className="pf-viewer-path">{selectedNode.filepath}</span>
                </div>
                <div className="pf-viewer-actions">
                  {fileContent && (
                    <>
                      <span className="pf-viewer-meta">{lines.length} lines</span>
                      {fileContent.size !== undefined && (
                        <span className="pf-viewer-meta">{formatSize(fileContent.size)}</span>
                      )}
                    </>
                  )}
                  <button
                    className={`pf-copy-btn ${copied ? 'copied' : ''}`}
                    onClick={handleCopy}
                    disabled={!fileContent?.content}
                  >
                    <Copy size={14} />
                    <span>{copied ? 'Copied!' : 'Copy'}</span>
                  </button>
                </div>
              </div>
              <div className="pf-viewer-body">
                {loadingContent && (
                  <div className="pf-center">
                    <Loader size={22} className="pf-spin" />
                    <span>Loading…</span>
                  </div>
                )}
                {!loadingContent && contentError && (
                  <div className="pf-center pf-error">
                    <AlertCircle size={22} />
                    <span>{contentError}</span>
                    <button className="pf-retry-btn" onClick={() => loadFileContent(selectedNode)}>
                      Retry
                    </button>
                  </div>
                )}
                {!loadingContent && !contentError && fileContent && (
                  <div className="pf-code-wrap">
                    <div className="pf-line-nums" aria-hidden="true">
                      {lines.map((_, i) => (
                        <span key={i} className="pf-line-num">{i + 1}</span>
                      ))}
                    </div>
                    <pre className="pf-code">
                      <code dangerouslySetInnerHTML={{ __html: highlight(fileContent.content, ext) }} />
                    </pre>
                  </div>
                )}
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default ProjectFilesPage;
