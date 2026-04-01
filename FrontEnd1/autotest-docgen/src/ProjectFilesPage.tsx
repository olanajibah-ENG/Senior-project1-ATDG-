import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Eye, FileText, Calendar, FolderOpen } from 'lucide-react';
import UnifiedApiService from './services/unifiedApiService';
import './GeneratedFilesPage.css';

interface GeneratedFile {
  _id: string;
  filename: string;
  file_type: 'pdf' | 'markdown';
  file_size: number;
  created_at: string;
  downloaded_count: number;
  analysis_id: string;
  explanation_id: string;
  project_id?: string;
}

const ProjectFilesPage: React.FC = () => {
  const { project_id } = useParams<{ project_id: string }>();
  const navigate = useNavigate();
  const [files, setFiles] = useState<GeneratedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [displayMode, setDisplayMode] = useState<'list' | 'display'>('list');
  const [selectedFile, setSelectedFile] = useState<GeneratedFile | null>(null);
  const [displayContent, setDisplayContent] = useState<string>('');
  const [loadingDisplay, setLoadingDisplay] = useState(false);
  const [projectName, setProjectName] = useState<string>('');

  // Fetch project-specific generated files
  const fetchFiles = async () => {
    if (!project_id) return;

    try {
      setLoading(true);
      const data = await UnifiedApiService.getProjectGeneratedFiles(project_id);
      setFiles(data.files || []);

      // Try to extract project name from files or use ID as fallback
      if (data.files && data.files.length > 0) {
        setProjectName(`Project ${project_id}`);
      } else {
        setProjectName(`Project ${project_id}`);
      }
    } catch (error) {
      console.error('Error fetching project files:', error);
      setError('Failed to load project files');
    } finally {
      setLoading(false);
    }
  };

  // Display file content using UnifiedApiService
  const displayFile = async (file: GeneratedFile) => {
    try {
      setLoadingDisplay(true);
      setSelectedFile(file);
      setDisplayMode('display');

      // Use UnifiedApiService for export
      const content = await UnifiedApiService.exportAnalysis(file.analysis_id, {
        mode: 'display',
        type: file.file_type === 'pdf' ? 'detailed' : 'low',
        format: file.file_type === 'pdf' ? 'pdf' : 'md'
      });

      // Convert blob to text if it's markdown
      if (file.file_type === 'markdown') {
        const text = await content.text();
        setDisplayContent(text);
      } else {
        setDisplayContent('PDF content cannot be displayed directly. Please download to view.');
      }
    } catch (error) {
      console.error('Error displaying file:', error);
      setError('Failed to load file content');
    } finally {
      setLoadingDisplay(false);
    }
  };

  // Download file using UnifiedApiService
  const downloadFile = async (file: GeneratedFile) => {
    try {
      console.log(' Starting download for file:', file.filename);

      // Use UnifiedApiService for download
      const blob = await UnifiedApiService.downloadGeneratedFile(file._id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      console.log(' File downloaded successfully:', file.filename);
    } catch (error) {
      console.error(' Error downloading file:', error);
      setError('Failed to download file. Please try again.');
    }
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format date
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  useEffect(() => {
    fetchFiles();
  }, [project_id]);

  if (loading) {
    return (
      <div className="generated-files-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading project files...</p>
        </div>
      </div>
    );
  }

  if (error && files.length === 0) {
    return (
      <div className="generated-files-page">
        <div className="error-container">
          <p>{error}</p>
          <button onClick={fetchFiles} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="generated-files-page">
      {displayMode === 'display' && selectedFile ? (
        <div className="display-mode">
          <div className="display-header">
            <button
              onClick={() => setDisplayMode('list')}
              className="back-button"
            >
              <ArrowLeft size={20} />
              <span>Back to Files</span>
            </button>
            <div className="display-actions">
              <h2>{selectedFile.filename}</h2>
              <button
                onClick={() => downloadFile(selectedFile)}
                className="download-button"
              >
                <Download size={16} />
                <span>Download</span>
              </button>
            </div>
          </div>

          {loadingDisplay ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading content...</p>
            </div>
          ) : (
            <div className="content-display">
              {selectedFile.file_type === 'markdown' ? (
                <div className="markdown-content">
                  <pre>{displayContent}</pre>
                </div>
              ) : (
                <div className="pdf-content">
                  <div className="pdf-placeholder">
                    <FileText size={48} />
                    <p>PDF content cannot be displayed directly</p>
                    <p>Please download the file to view its contents</p>
                    <button
                      onClick={() => downloadFile(selectedFile)}
                      className="download-button"
                    >
                      <Download size={16} />
                      <span>Download PDF</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="page-header">
            <button
              onClick={() => navigate('/dashboard')}
              className="back-button"
            >
              <ArrowLeft size={20} />
              <span>Back to Dashboard</span>
            </button>
            <div className="page-title">
              <div className="project-info">
                <FolderOpen size={24} style={{ marginRight: '8px' }} />
                <h1>{projectName} - Files</h1>
              </div>
              <p>View and download generated documentation files for this project</p>
            </div>
          </div>

          <div className="files-list">
            {files.length === 0 ? (
              <div className="empty-state">
                <FileText size={64} />
                <h3>No generated files found for this project</h3>
                <p>Upload some code files and generate documentation to see them here</p>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="dashboard-button"
                >
                  Go to Dashboard
                </button>
              </div>
            ) : (
              <div className="files-grid">
                {files.map((file) => (
                  <div key={file._id} className="file-card">
                    <div className="file-main-info">
                      <div className="file-icon">
                        <FileText
                          size={28}
                          className={file.file_type === 'pdf' ? 'pdf-icon' : 'markdown-icon'}
                        />
                      </div>

                      <div className="file-info">
                        <h3 title={file.filename}>{file.filename}</h3>
                        <div className="file-meta">
                          <span className="file-type">{file.file_type.toUpperCase()}</span>
                          <span className="file-size">{formatFileSize(file.file_size)}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="file-date">
                        <Calendar size={14} />
                        <span>{formatDate(file.created_at)}</span>
                      </div>
                      <div className="downloads-count">
                        <Download size={14} />
                        <span>Downloaded {file.downloaded_count} times</span>
                      </div>
                    </div>

                    <div className="file-actions">
                      <button
                        onClick={() => displayFile(file)}
                        className="display-button"
                        title="Display content"
                      >
                        <Eye size={16} />
                        <span>View</span>
                      </button>
                      <button
                        onClick={() => downloadFile(file)}
                        className="download-button"
                        title="Download file"
                      >
                        <Download size={16} />
                        <span>Download</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ProjectFilesPage;
