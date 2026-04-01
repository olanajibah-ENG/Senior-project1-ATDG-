import React, { useState, useEffect } from 'react';
import { Upload, Code, Zap, CheckCircle, XCircle, AlertCircle, X, FolderOpen, Archive, Github, Trash2, Clock, Network, FileText, GitBranch, Activity } from 'lucide-react';
import type { Project } from '../../services/api.service';
import type { DependencyGraph, CrossFileContext } from '../../services/extendedApi.service';
import { i18n } from '../../utils/i18n';
import extendedApiService from '../../services/extendedApi.service';
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
  const [githubFetched, setGithubFetched] = useState(false);
  const [githubFetching, setGithubFetching] = useState(false);

  // Project insights state
  const [projectInsights] = useState<any>(null);
  const [, setDependencyGraph] = useState<DependencyGraph | null>(null);
  const [, setCrossFileContext] = useState<CrossFileContext | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [, setInsightsError] = useState<string | null>(null);

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
      // Load project insights when ZIP is uploaded
      loadProjectInsights();
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
      // Load project insights when ZIP is dropped
      loadProjectInsights();
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

    try {
      // Simulate GitHub fetch (replace with actual API call)
      await new Promise(resolve => setTimeout(resolve, 2000));
      setGithubFetched(true);
      loadProjectInsights();
    } catch (error) {
      setValidationError('Failed to fetch GitHub repository');
      setGithubFetched(false);
    } finally {
      setGithubFetching(false);
    }
  };

  // Load project insights from backend APIs
  const loadProjectInsights = async () => {
    if (selectedFiles.length === 0 && !zipFile && !githubFetched) {
      setInsightsError('No files available for analysis');
      return;
    }

    setInsightsLoading(true);
    setInsightsError(null);

    try {
      // Prepare file names for analysis
      const fileNames = selectedFiles.map(file => file.name);

      // Get dependency graph from backend
      try {
        const dependencyData = await extendedApiService.getDependencyGraph(project.id, fileNames);
        setDependencyGraph(dependencyData);
      } catch (error) {
        console.error('Failed to load dependency graph:', error);
        // Set mock data as fallback
        setDependencyGraph({
          nodes: [
            { id: '1', name: 'main.py', type: 'file', language: 'python', file_path: '/main.py' },
            { id: '2', name: 'utils.py', type: 'file', language: 'python', file_path: '/utils.py' },
            { id: '3', name: 'config', type: 'variable', language: 'python', file_path: '/main.py' }
          ],
          edges: [
            { from: '1', to: '2', type: 'imports', strength: 0.8 },
            { from: '1', to: '3', type: 'uses', strength: 0.6 }
          ],
          metadata: {
            total_files: selectedFiles.length,
            total_dependencies: 2,
            complexity_score: 0.7
          }
        });
      }

      // Get cross-file context from backend
      try {
        const contextData = await extendedApiService.getCrossFileContext(project.id, fileNames);
        setCrossFileContext(contextData);
      } catch (error) {
        console.error('Failed to load cross-file context:', error);
        // Set mock data as fallback
          setCrossFileContext({
            fileContexts: [],
            file_relationships: [
              { from: 'main.py', to: 'utils.py', type: 'imports' },
              { from: 'config.py', to: 'main.py', type: 'calls' }
            ]
          });
      }

    } catch (error) {
      console.error('Failed to load project insights:', error);
      setInsightsError('Failed to load project insights');
    } finally {
      setInsightsLoading(false);
    }
  };

  // Auto-load insights when files are selected
  useEffect(() => {
    if (selectedFiles.length > 0 || zipFile || githubFetched) {
      loadProjectInsights();
    }
  }, [selectedFiles, zipFile, githubFetched]);

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
    return zipFile !== null || (githubFetched && githubUrl.trim());
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
            {/* Left Panel - Project Insights */}
            {(zipFile !== null || (githubFetched && githubUrl.trim())) && (
              <div className="insights-panel">
                <div className="insights-panel-content">
                  <div className="insights-panel-title">
                    <Network size={18} />
                    Project Insights
                  </div>

                  {insightsLoading ? (
                    <div className="insights-loading">
                      <div className="spinner-small"></div>
                      <span>Analyzing project...</span>
                    </div>
                  ) : projectInsights ? (
                    <div className="insights-content">
                      {/* Dependency Summary */}
                      <div className="insight-section">
                        <h4 className="insight-section-title">
                          <Activity size={16} />
                          Dependency Summary
                        </h4>
                        <div className="insight-content">
                          <div className="dependency-summary">
                            <div className="summary-item">
                              <span className="summary-label">Total Files:</span>
                              <span className="summary-value">{projectInsights.totalFiles || selectedFiles.length}</span>
                            </div>
                            <div className="summary-item">
                              <span className="summary-label">Dependencies:</span>
                              <span className="summary-value">{projectInsights.dependencies?.length || 0}</span>
                            </div>
                            <div className="summary-item">
                              <span className="summary-label">Language:</span>
                              <span className="summary-value">{projectInsights.language || 'Auto-detected'}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Dependency Order */}
                      {projectInsights.dependencyOrder && projectInsights.dependencyOrder.length > 0 && (
                        <div className="insight-section">
                          <h4 className="insight-section-title">
                            <GitBranch size={16} />
                            Dependency Order
                          </h4>
                          <div className="insight-content">
                            <div className="dependency-order">
                              {projectInsights.dependencyOrder.slice(0, 5).map((file: string, index: number) => (
                                <div key={index} className="order-item">
                                  <span className="order-number">{index + 1}</span>
                                  <span className="order-file">{file}</span>
                                </div>
                              ))}
                              {projectInsights.dependencyOrder.length > 5 && (
                                <div className="order-more">+{projectInsights.dependencyOrder.length - 5} more files</div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* File Context Viewer */}
                      {projectInsights.crossFileContext && projectInsights.crossFileContext.length > 0 && (
                        <div className="insight-section">
                          <h4 className="insight-section-title">
                            <FileText size={16} />
                            Cross-File Context
                          </h4>
                          <div className="insight-content">
                            <div className="context-viewer">
                              {projectInsights.crossFileContext.slice(0, 3).map((context: any, index: number) => (
                                <div key={index} className="context-item">
                                  <div className="context-file">{context.file}</div>
                                  <div className="context-details">
                                    <span className="context-type">{context.type}</span>
                                    <span className="context-references">{context.references} refs</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Simple Dependency Graph */}
                      {projectInsights.dependencies && projectInsights.dependencies.length > 0 && (
                        <div className="insight-section">
                          <h4 className="insight-section-title">
                            <Network size={16} />
                            Dependencies
                          </h4>
                          <div className="insight-content">
                            <div className="dependency-graph">
                              {projectInsights.dependencies.slice(0, 8).map((dep: any, index: number) => (
                                <div key={index} className="dependency-item">
                                  <div className="dependency-name">{dep.name}</div>
                                  <div className="dependency-type">{dep.type}</div>
                                </div>
                              ))}
                              {projectInsights.dependencies.length > 8 && (
                                <div className="dependency-more">+{projectInsights.dependencies.length - 8} more</div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="insights-placeholder">
                      <Network size={32} />
                      <p>Upload files to see project insights</p>
                    </div>
                  )}
                </div>
              </div>
            )}

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
                        <div className="github-input-group">
                          <input
                            id="github-url"
                            type="url"
                            className="code-upload-input"
                            value={githubUrl}
                            onChange={(e) => setGithubUrl(e.target.value)}
                            placeholder="https://github.com/username/repository"
                            disabled={isProcessing || githubFetching}
                          />
                          <button
                            onClick={handleGithubFetch}
                            disabled={isProcessing || githubFetching || !githubUrl.trim()}
                            className="github-fetch-btn"
                          >
                            {githubFetching ? (
                              <>
                                <div className="button-spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div>
                                Fetching...
                              </>
                            ) : githubFetched ? (
                              <>
                                <CheckCircle size={16} />
                                Fetched
                              </>
                            ) : (
                              <>
                                <Github size={16} />
                                Fetch
                              </>
                            )}
                          </button>
                        </div>
                        <p className="code-upload-hint">
                          <AlertCircle size={14} />
                          Enter the URL of a public GitHub repository to fetch the source code
                        </p>
                        {githubFetched && (
                          <div className="form-feedback success">
                            <CheckCircle size={14} />
                            Successfully fetched repository: {githubUrl}
                          </div>
                        )}
                      </div>
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
