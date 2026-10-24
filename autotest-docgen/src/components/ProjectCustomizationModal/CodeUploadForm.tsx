import React, { useState, useEffect } from 'react';
import { Upload, Code, Zap, CheckCircle, XCircle, AlertCircle, X, FolderOpen, Archive, Github, Trash2, Clock, FileText } from 'lucide-react';
import type { Project } from '../../services/api.service';
import UnifiedApiService from '../../services/unifiedApiService';
import { i18n } from '../../utils/i18n';
import './CodeUploadForm.css';

interface CodeUploadFormProps {
  project: Project;
  isProcessing: boolean;
  apiError: string | null;
  onGenerateDiagram: (payload: {
    projectId: string;
    codeName: string;
    fileName: string;
    language: 'auto-detect' | 'python' | 'java' | 'javascript' | 'typescript' | 'csharp' | 'go' | 'php' | 'cpp' | 'rust' | 'ruby' | 'swift' | 'kotlin' | 'scala' | 'dart' | 'r';
    version: string;
    codeText: string;
    file: File | null;
    files?: File[];
    githubUrl?: string;
    zipFile?: File;
  }) => Promise<void>;
  onClose: () => void;
}

const CodeUploadForm: React.FC<CodeUploadFormProps> = ({
  project,
  isProcessing,
  apiError,
  onGenerateDiagram,
  onClose,
}) => {
  const [codeLanguage] = useState<'auto-detect' | 'python' | 'java' | 'javascript' | 'typescript' | 'csharp' | 'go' | 'php' | 'cpp' | 'rust' | 'ruby' | 'swift' | 'kotlin' | 'scala' | 'dart' | 'r'>('auto-detect');
  const [version] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  // Tab state
  const [activeTab, setActiveTab] = useState<'local-files' | 'zip-upload' | 'github-repo'>('local-files');

  // Local files state
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [filesDragOver, setFilesDragOver] = useState(false);
  const [fileUploads, setFileUploads] = useState<Map<string, { progress: number; status: 'pending' | 'uploading' | 'done' | 'error'; error?: string }>>(new Map());
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // ZIP upload state
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [zipDragOver, setZipDragOver] = useState(false);

  // GitHub repo state
  const [githubUrl, setGithubUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [githubToken, setGithubToken] = useState('');
  const [githubFetched, setGithubFetched] = useState(false);
  const [githubFetching, setGithubFetching] = useState(false);
  const [repoId, setRepoId] = useState<string | null>(null);

  // Local files handlers
  const handleLocalFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(file => {
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (codeLanguage === 'auto-detect') {
        return ['.py', '.java', '.js', '.ts', '.cs', '.go', '.php', '.cpp', '.c', '.h', '.rs', '.rb', '.swift', '.kt', '.scala', '.dart', '.r'].includes(extension);
      } else {
        const languageExtensions: Record<string, string[]> = {
          'python': ['.py'],
          'java': ['.java'],
          'javascript': ['.js'],
          'typescript': ['.ts'],
          'csharp': ['.cs'],
          'go': ['.go'],
          'php': ['.php'],
          'cpp': ['.cpp', '.c', '.h'],
          'rust': ['.rs'],
          'ruby': ['.rb'],
          'swift': ['.swift'],
          'kotlin': ['.kt'],
          'scala': ['.scala'],
          'dart': ['.dart'],
          'r': ['.r']
        };
        return languageExtensions[codeLanguage]?.includes(extension) || false;
      }
    });

    // Add new files and initialize their upload status
    const newFiles = validFiles.filter(file => !selectedFiles.some(existing => existing.name === file.name && existing.size === file.size));
    setSelectedFiles(prev => [...prev, ...newFiles]);

    // Initialize upload status for new files
    const newUploads = new Map(fileUploads);
    newFiles.forEach(file => {
      newUploads.set(`${file.name}-${file.size}`, { progress: 0, status: 'pending' });
    });
    setFileUploads(newUploads);
  };

  const handleFilesDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setFilesDragOver(true);
  };

  const handleFilesDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setFilesDragOver(false);
  };

  const handleFilesDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setFilesDragOver(false);

    const files = Array.from(e.dataTransfer.files || []);
    const validFiles = files.filter(file => {
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (codeLanguage === 'auto-detect') {
        return ['.py', '.java', '.js', '.ts', '.cs', '.go', '.php', '.cpp', '.c', '.h', '.rs', '.rb', '.swift', '.kt', '.scala', '.dart', '.r'].includes(extension);
      } else {
        const languageExtensions: Record<string, string[]> = {
          'python': ['.py'],
          'java': ['.java'],
          'javascript': ['.js'],
          'typescript': ['.ts'],
          'csharp': ['.cs'],
          'go': ['.go'],
          'php': ['.php'],
          'cpp': ['.cpp', '.c', '.h'],
          'rust': ['.rs'],
          'ruby': ['.rb'],
          'swift': ['.swift'],
          'kotlin': ['.kt'],
          'scala': ['.scala'],
          'dart': ['.dart'],
          'r': ['.r']
        };
        return languageExtensions[codeLanguage]?.includes(extension) || false;
      }
    });

    // Add new files and initialize their upload status
    const newFiles = validFiles.filter(file => !selectedFiles.some(existing => existing.name === file.name && existing.size === file.size));
    setSelectedFiles(prev => [...prev, ...newFiles]);

    // Initialize upload status for new files
    const newUploads = new Map(fileUploads);
    newFiles.forEach(file => {
      newUploads.set(`${file.name}-${file.size}`, { progress: 0, status: 'pending' });
    });
    setFileUploads(newUploads);
  };

  const removeFile = (index: number) => {
    const file = selectedFiles[index];
    const fileKey = `${file.name}-${file.size}`;

    setSelectedFiles(prev => prev.filter((_, i) => i !== index));

    // Remove from upload tracking
    const newUploads = new Map(fileUploads);
    newUploads.delete(fileKey);
    setFileUploads(newUploads);
  };

  const clearAllFiles = () => {
    setSelectedFiles([]);
    setFileUploads(new Map());
    setIsUploading(false);
    setUploadProgress(0);
  };

  const uploadFiles = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Simulate file upload with progress tracking
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const fileKey = `${file.name}-${file.size}`;

        // Update status to uploading
        const newUploads = new Map(fileUploads);
        newUploads.set(fileKey, { progress: 0, status: 'uploading' });
        setFileUploads(new Map(newUploads));

        // Simulate upload progress
        for (let progress = 0; progress <= 100; progress += 10) {
          await new Promise(resolve => setTimeout(resolve, 100));
          const updatedUploads = new Map(fileUploads);
          updatedUploads.set(fileKey, { progress, status: 'uploading' });
          setFileUploads(new Map(updatedUploads));

          // Update overall progress
          const overallProgress = Math.round(((i * 100) + progress) / selectedFiles.length);
          setUploadProgress(overallProgress);
        }

        // Mark as done
        const completedUploads = new Map(fileUploads);
        completedUploads.set(fileKey, { progress: 100, status: 'done' });
        setFileUploads(new Map(completedUploads));
      }
    } catch (error) {
      // Handle upload error
      const errorUploads = new Map(fileUploads);
      selectedFiles.forEach(file => {
        const fileKey = `${file.name}-${file.size}`;
        if (errorUploads.get(fileKey)?.status === 'uploading') {
          errorUploads.set(fileKey, { progress: 0, status: 'error', error: 'Upload failed' });
        }
      });
      setFileUploads(errorUploads);
    } finally {
      setIsUploading(false);
    }
  };

  const cancelUpload = () => {
    setIsUploading(false);

    // Reset uploading files to pending
    const resetUploads = new Map(fileUploads);
    selectedFiles.forEach(file => {
      const fileKey = `${file.name}-${file.size}`;
      const current = resetUploads.get(fileKey);
      if (current?.status === 'uploading') {
        resetUploads.set(fileKey, { progress: 0, status: 'pending' });
      }
    });
    setFileUploads(resetUploads);
    setUploadProgress(0);
  };

  // ZIP handlers
  const handleZipChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    if (selected && selected.name.endsWith('.zip')) {
      setZipFile(selected);
      setValidationError(null);
    } else if (selected) {
      setValidationError('Please select a valid ZIP file');
    }
  };

  const handleZipDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setZipDragOver(true);
  };

  const handleZipDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setZipDragOver(false);
  };

  const handleZipDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setZipDragOver(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.name.endsWith('.zip')) {
      setZipFile(droppedFile);
      setValidationError(null);
    } else if (droppedFile) {
      setValidationError('Please select a valid ZIP file');
    }
  };

  // GitHub handlers
  const handleGithubFetch = async () => {
    if (!githubUrl.trim()) {
      setValidationError('Please enter a GitHub repository URL');
      return;
    }

    setGithubFetching(true);
    setValidationError(null);
    setGithubFetched(false);

    try {
      const payload = {
        repo_url: githubUrl.trim(),
        branch: branch.trim() || 'main',
        github_token: githubToken.trim() || '',
      };

      console.log('Connecting to GitHub with Project ID:', project.id);
      const response = await UnifiedApiService.connectGithubRepo(project.id, payload);
      console.log('GitHub Connect Response:', response);

      if (response && response.repo_id) {
        setRepoId(response.repo_id);
        setGithubFetched(true);
      } else {
        throw new Error('Connection succeeded but no repo_id returned.');
      }
    } catch (error: any) {
      console.error('GitHub connection error:', error);
      // Extract the actual backend error message
      const backendError =
        error.response?.data?.detail ||
        error.response?.data?.error ||
        error.response?.data?.message ||
        (typeof error.response?.data === 'string' ? error.response.data : null) ||
        JSON.stringify(error.response?.data) ||
        'Failed to connect repository. Check your URL and Token.';
      const errorMsg = backendError;
      console.error('Backend error detail:', error.response?.data);
      setValidationError(errorMsg);
      setGithubFetched(false);
    } finally {
      setGithubFetching(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateFileName = () => {
    // File name validation is now automatic based on selected files
    return null;
  };

  const buildPayload = () => {
    setValidationError(null);

    // Validate file name (now automatic)
    const fileNameError = validateFileName();
    if (fileNameError) {
      setValidationError(fileNameError);
      return;
    }

    // Validate that at least one input method has content
    const hasLocalFiles = selectedFiles.length > 0;
    const hasZipFile = zipFile !== null;
    const hasGithubRepo = githubFetched && githubUrl.trim();

    if (!hasLocalFiles && !hasZipFile && !hasGithubRepo) {
      setValidationError('Please select files, upload a ZIP, or provide a GitHub repository');
      return;
    }

    return {
      projectId: project.id,
      codeName: selectedFiles[0]?.name || zipFile?.name || 'github-repo',
      fileName: selectedFiles[0]?.name || zipFile?.name || 'github-repo',
      language: codeLanguage,
      version: version.trim(),
      codeText: '', // Empty since we removed paste functionality
      file: null, // Single file not used in new design
      files: hasLocalFiles ? selectedFiles : undefined,
      zipFile: hasZipFile ? zipFile : undefined,
      githubUrl: hasGithubRepo ? githubUrl : undefined,
    };
  };

  const handleDiagramClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    console.log('🔵 handleDiagramClick called');
    const payload = buildPayload();
    console.log('🟢 Payload built:', payload);

    if (payload) {
      console.log('🟡 Calling onGenerateDiagram...');
      await onGenerateDiagram(payload);
      console.log('🟠 onGenerateDiagram finished');
    } else {
      console.log('🔴 Payload validation failed');
    }
  };

  const isStartAnalysisEnabled = () => {
    return selectedFiles.length > 0 || zipFile !== null || (githubFetched && githubUrl.trim());
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-lg modal-wide" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title">
            <Code size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            {project.title}
          </div>
          <button
            className="modal-close-btn"
            onClick={onClose}
            title="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          <div className="two-column-layout">
            {/* Right Panel */}
            <div className="right-panel">
              <div className="code-upload-container">
                <div className="code-upload-header">
                  <h2 className="code-upload-title">
                    <Zap size={24} style={{ marginRight: '12px', verticalAlign: 'middle' }} />
                    Code Upload
                  </h2>
                  <p className="code-upload-subtitle">
                    {project.description || 'Upload your code to generate class diagram'}
                  </p>
                </div>

                {(apiError || validationError) && (
                  <div className="form-feedback error">
                    <AlertCircle size={14} />
                    {apiError || validationError}
                  </div>
                )}

                {/* Tabs */}
                <div className="upload-tabs">
                  <button
                    className={`tab-button ${activeTab === 'local-files' ? 'active' : ''}`}
                    onClick={() => setActiveTab('local-files')}
                  >
                    <FolderOpen size={16} />
                    Local Files
                  </button>
                  <button
                    className={`tab-button ${activeTab === 'zip-upload' ? 'active' : ''}`}
                    onClick={() => setActiveTab('zip-upload')}
                  >
                    <Archive size={16} />
                    Upload ZIP
                  </button>
                  <button
                    className={`tab-button ${activeTab === 'github-repo' ? 'active' : ''}`}
                    onClick={() => setActiveTab('github-repo')}
                  >
                    <Github size={16} />
                    GitHub Repo
                  </button>
                </div>

                {/* Tab Content */}
                <div className="tab-content">
                  {activeTab === 'local-files' && (
                    <div className="local-files-tab">
                      <div className="local-files-horizontal-layout">
                        {/* Left side: Drag & Drop Area */}
                        <div className="upload-area-section">
                          <div className="code-upload-group">
                            <div className="upload-area">
                              <input
                                id="local-files-input"
                                type="file"
                                multiple
                                className="upload-input"
                                accept={codeLanguage === 'auto-detect' ? '.py,.java,.js,.ts,.cs,.go,.php,.cpp,.c,.h,.rs,.rb,.swift,.kt,.scala,.dart,.r' : (() => {
                                  const languageExtensions: Record<string, string> = {
                                    'python': '.py',
                                    'java': '.java',
                                    'javascript': '.js',
                                    'typescript': '.ts',
                                    'csharp': '.cs',
                                    'go': '.go',
                                    'php': '.php',
                                    'cpp': '.cpp,.c,.h',
                                    'rust': '.rs',
                                    'ruby': '.rb',
                                    'swift': '.swift',
                                    'kotlin': '.kt',
                                    'scala': '.scala',
                                    'dart': '.dart',
                                    'r': '.r'
                                  };
                                  return languageExtensions[codeLanguage] || '';
                                })()}
                                onChange={handleLocalFilesChange}
                                disabled={isProcessing || isUploading}
                              />
                              <label
                                htmlFor="local-files-input"
                                className={`upload-label ${filesDragOver ? 'drag-over' : ''}`}
                                onDragOver={handleFilesDragOver}
                                onDragLeave={handleFilesDragLeave}
                                onDrop={handleFilesDrop}
                              >
                                <div className="upload-icon">
                                  <Upload size={64} />
                                </div>
                                <div className="upload-text">
                                  <h3>Drag & Drop files here</h3>
                                  <p>or click to browse</p>
                                </div>
                                <div className="upload-hint">
                                  {codeLanguage === 'auto-detect'
                                    ? 'Supports: .py, .java, .js, .ts, .cs, .go, .php, .cpp, .c, .h, .rs, .rb, .swift, .kt, .scala, .dart, .r'
                                    : (() => {
                                      const languageInfo: Record<string, { name: string; extensions: string }> = {
                                        'python': { name: 'Python files', extensions: '.py' },
                                        'java': { name: 'Java files', extensions: '.java' },
                                        'javascript': { name: 'JavaScript files', extensions: '.js' },
                                        'typescript': { name: 'TypeScript files', extensions: '.ts' },
                                        'csharp': { name: 'C# files', extensions: '.cs' },
                                        'go': { name: 'Go files', extensions: '.go' },
                                        'php': { name: 'PHP files', extensions: '.php' },
                                        'cpp': { name: 'C++ files', extensions: '.cpp, .c, .h' },
                                        'rust': { name: 'Rust files', extensions: '.rs' },
                                        'ruby': { name: 'Ruby files', extensions: '.rb' },
                                        'swift': { name: 'Swift files', extensions: '.swift' },
                                        'kotlin': { name: 'Kotlin files', extensions: '.kt' },
                                        'scala': { name: 'Scala files', extensions: '.scala' },
                                        'dart': { name: 'Dart files', extensions: '.dart' },
                                        'r': { name: 'R files', extensions: '.r' }
                                      };
                                      const info = languageInfo[codeLanguage];
                                      return info ? `Supports: ${info.name} (${info.extensions})` : 'Supports: Code files';
                                    })()}
                                </div>
                              </label>
                            </div>
                          </div>
                        </div>

                        {/* Right side: File List */}
                        {selectedFiles.length > 0 && (
                          <div className="file-list-section">
                            <div className="file-list-container">
                              <div className="file-list-header">
                                <div className="file-list-title">
                                  <h4>Selected Files ({selectedFiles.length})</h4>
                                  {isUploading && (
                                    <div className="overall-progress">
                                      <div className="progress-bar">
                                        <div
                                          className="progress-fill"
                                          style={{ width: `${uploadProgress}%` }}
                                        ></div>
                                      </div>
                                      <span className="progress-text">{uploadProgress}%</span>
                                    </div>
                                  )}
                                </div>
                                <button onClick={clearAllFiles} className="clear-all-btn" disabled={isUploading}>
                                  <Trash2 size={14} />
                                  Clear All
                                </button>
                              </div>

                              <div className="file-list">
                                {selectedFiles.map((file, index) => {
                                  const fileKey = `${file.name}-${file.size}`;
                                  const uploadStatus = fileUploads.get(fileKey) || { progress: 0, status: 'pending' as const };

                                  return (
                                    <div key={fileKey} className="file-item">
                                      <div className="file-info">
                                        <div className="file-details">
                                          <span className="file-name">{file.name}</span>
                                          <span className="file-size">{formatFileSize(file.size)}</span>
                                        </div>

                                        <div className="file-status">
                                          {uploadStatus.status === 'pending' && (
                                            <div className="status-indicator pending">
                                              <Clock size={14} />
                                              <span>Pending</span>
                                            </div>
                                          )}
                                          {uploadStatus.status === 'uploading' && (
                                            <div className="status-indicator uploading">
                                              <div className="spinner-small"></div>
                                              <span>Uploading</span>
                                            </div>
                                          )}
                                          {uploadStatus.status === 'done' && (
                                            <div className="status-indicator done">
                                              <CheckCircle size={14} />
                                              <span>Done</span>
                                            </div>
                                          )}
                                          {uploadStatus.status === 'error' && (
                                            <div className="status-indicator error">
                                              <XCircle size={14} />
                                              <span>Error</span>
                                            </div>
                                          )}
                                        </div>
                                      </div>

                                      <div className="file-progress">
                                        {uploadStatus.status === 'uploading' && (
                                          <div className="progress-bar">
                                            <div
                                              className="progress-fill"
                                              style={{ width: `${uploadStatus.progress}%` }}
                                            ></div>
                                          </div>
                                        )}
                                        {uploadStatus.status === 'done' && (
                                          <div className="progress-bar complete">
                                            <div className="progress-fill" style={{ width: '100%' }}></div>
                                          </div>
                                        )}
                                        {uploadStatus.status === 'error' && (
                                          <div className="progress-bar error">
                                            <div className="progress-fill" style={{ width: `${uploadStatus.progress}%` }}></div>
                                          </div>
                                        )}
                                      </div>

                                      <button
                                        onClick={() => removeFile(index)}
                                        className="remove-file-btn"
                                        disabled={isUploading && uploadStatus.status === 'uploading'}
                                      >
                                        <X size={14} />
                                      </button>
                                    </div>
                                  );
                                })}
                              </div>

                              {/* Upload Controls */}
                              <div className="upload-controls">
                                {!isUploading ? (
                                  <button
                                    onClick={uploadFiles}
                                    disabled={selectedFiles.length === 0 || isProcessing}
                                    className="upload-btn primary full-width"
                                  >
                                    <Upload size={16} />
                                    Upload Files
                                  </button>
                                ) : (
                                  <button
                                    onClick={cancelUpload}
                                    className="upload-btn secondary full-width"
                                  >
                                    <XCircle size={16} />
                                    Cancel Upload
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {activeTab === 'zip-upload' && (
                    <div className="zip-upload-tab">
                      <div className="code-upload-group full-width">
                        <div className="code-upload-file-group">
                          <input
                            id="zip-file-input"
                            type="file"
                            className="code-upload-file-input"
                            accept=".zip"
                            onChange={handleZipChange}
                            disabled={isProcessing}
                          />
                          <label
                            htmlFor="zip-file-input"
                            className={`code-upload-file-label ${zipFile ? 'code-upload-file-selected' : ''} ${zipDragOver ? 'drag-over' : ''}`}
                            onDragOver={handleZipDragOver}
                            onDragLeave={handleZipDragLeave}
                            onDrop={handleZipDrop}
                          >
                            <Archive size={48} className="code-upload-file-icon" />
                            <div className="code-upload-file-text">
                              {zipFile ? (
                                <>
                                  <CheckCircle size={20} style={{ marginRight: '8px', color: '#28a745' }} />
                                  {zipFile.name}
                                </>
                              ) : (
                                '📁 Drag & drop ZIP file here or click to browse'
                              )}
                            </div>
                            <div className="code-upload-file-subtext">
                              📦 ZIP files • Max 50MB
                              {zipFile && (
                                <span style={{ marginLeft: '8px', color: '#28a745' }}>
                                  ✓ {formatFileSize(zipFile.size)}
                                </span>
                              )}
                            </div>
                          </label>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'github-repo' && (
                    <div className="github-repo-tab">
                      <div className="code-upload-group full-width">
                        <label htmlFor="github-url" className="code-upload-label">
                          <Github size={16} />
                          GitHub Repository URL
                        </label>
                        <input
                          id="github-url"
                          type="url"
                          className="code-upload-input"
                          value={githubUrl}
                          onChange={(e) => { setGithubUrl(e.target.value); setGithubFetched(false); setRepoId(null); }}
                          placeholder="https://github.com/username/repository"
                          disabled={isProcessing || githubFetching}
                        />
                      </div>

                      <div className="github-form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
                        <div className="code-upload-group">
                          <label htmlFor="github-branch" className="code-upload-label">
                            Branch
                          </label>
                          <input
                            id="github-branch"
                            type="text"
                            className="code-upload-input"
                            value={branch}
                            onChange={(e) => setBranch(e.target.value)}
                            placeholder="main"
                            disabled={isProcessing || githubFetching}
                          />
                        </div>

                        <div className="code-upload-group">
                          <label htmlFor="github-token" className="code-upload-label">
                            Access Token (Optional)
                          </label>
                          <input
                            id="github-token"
                            type="password"
                            className="code-upload-input"
                            value={githubToken}
                            onChange={(e) => setGithubToken(e.target.value)}
                            placeholder="ghp_xxxx..."
                            disabled={isProcessing || githubFetching}
                          />
                        </div>
                      </div>

                      <p className="code-upload-hint" style={{ marginTop: '8px' }}>
                        <AlertCircle size={14} />
                        Required for private repositories. Ensure token has 'repo' scope.
                      </p>

                      <button
                        onClick={handleGithubFetch}
                        disabled={isProcessing || githubFetching || !githubUrl.trim()}
                        className="github-fetch-btn"
                        style={{ marginTop: '16px', width: '100%' }}
                      >
                        {githubFetching ? (
                          <>
                            <div className="button-spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div>
                            Connecting...
                          </>
                        ) : githubFetched ? (
                          <>
                            <CheckCircle size={16} />
                            Connected
                          </>
                        ) : (
                          <>
                            <Github size={16} />
                            Connect Repository
                          </>
                        )}
                      </button>

                      {githubFetched && (
                        <div className="form-feedback success" style={{ marginTop: '12px' }}>
                          <CheckCircle size={14} />
                          Successfully connected: {githubUrl}
                          {repoId && <span style={{ marginLeft: '8px', opacity: 0.7 }}>(repo_id: {repoId})</span>}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="code-upload-actions">
                  <button
                    type="button"
                    onClick={handleDiagramClick}
                    disabled={isProcessing || !isStartAnalysisEnabled()}
                    className="code-upload-btn code-upload-btn-primary"
                  >
                    <Zap size={20} style={{ marginRight: '8px' }} />
                    {isProcessing ? (
                      <>
                        <div className="button-spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }}></div>
                        {i18n.t('code.processing')}
                      </>
                    ) : (
                      <>
                        <CheckCircle size={20} style={{ marginRight: '8px' }} />
                        Upload Files
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={onClose}
                    disabled={isProcessing}
                    className="code-upload-btn code-upload-btn-secondary"
                  >
                    <XCircle size={20} style={{ marginRight: '8px' }} />
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodeUploadForm;
