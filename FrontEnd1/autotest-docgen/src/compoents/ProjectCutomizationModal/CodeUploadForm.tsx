import React, { useState } from 'react';
import { Upload, FileText, Code, Settings, Zap, CheckCircle, XCircle, AlertCircle, X } from 'lucide-react';
import type { Project } from '../../services/api.service';
import { i18n } from '../../utils/i18n';
import { useLanguage } from '../../context/LanguageContext';
import './CodeUploadForm.css';

interface CodeUploadFormProps {
  project: Project;
  isProcessing: boolean;
  apiError: string | null;
  onGenerateDiagram: (payload: {
    projectId: string;
    codeName: string;
    fileName: string;
    language: 'python' | 'java';
    version: string;
    codeText: string;
    file: File | null;
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
  const { t } = useLanguage();
  const [fileName, setFileName] = useState('');
  const [codeLanguage, setCodeLanguage] = useState<'python' | 'java'>('python');
  const [version, setVersion] = useState('');
  const [codeText, setCodeText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleCodeTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setCodeText(newText);

    // If code is being pasted/typed and no file is uploaded, clear file name
    if (newText.trim() && !file) {
      setFileName('');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    validateAndSetFile(selected);
  };

  const validateAndSetFile = (selectedFile: File | null) => {
    if (selectedFile) {
      // Check file size (10MB limit)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (selectedFile.size > maxSize) {
        setValidationError('File size must be less than 10MB');
        return;
      }

      // Check file type
      const allowedExtensions = codeLanguage === 'python' ? ['.py'] : ['.java'];
      const fileExtension = '.' + selectedFile.name.split('.').pop()?.toLowerCase();

      if (!allowedExtensions.includes(fileExtension)) {
        setValidationError(`Only ${codeLanguage} files (${allowedExtensions.join(', ')}) are allowed`);
        return;
      }

      setFile(selectedFile);
      // Always set file name with full extension when a file is uploaded
      setFileName(selectedFile.name); // Keep full name with extension
      setValidationError(null);
    } else {
      setFile(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  };

  const validateFileName = (name: string) => {
    if (!name.trim()) {
      // Only require file name if code is pasted but no file is uploaded
      if (codeText.trim() && !file) {
        return 'Please enter a file name with .py or .java extension';
      }
      return null;
    }

    const requiredExtension = codeLanguage === 'python' ? '.py' : '.java';
    if (!name.endsWith(requiredExtension)) {
      return `File name must end with ${requiredExtension} extension for ${codeLanguage}`;
    }

    return null;
  };

  const handleFileNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newName = e.target.value;
    setFileName(newName);

    // Validate file name
    const error = validateFileName(newName);
    if (error) {
      setValidationError(error);
    } else {
      // Clear validation error if it was related to file name
      if (validationError === validateFileName(fileName)) {
        setValidationError(null);
      }
    }
  };

  const buildPayload = () => {
    setValidationError(null);

    // Validate file name extension
    const fileNameError = validateFileName(fileName);
    if (fileNameError) {
      setValidationError(fileNameError);
      return;
    }

    // Validate that either file or code text is provided
    if (!file && !codeText.trim()) {
      setValidationError('Please provide either a code file or enter code manually');
      return;
    }

    // If file is provided, validate code text matches language
    if (file && codeText.trim()) {
      if (codeLanguage === 'python' && !codeText.includes('def ') && !codeText.includes('class ')) {
        setValidationError('Python code should contain functions (def) or classes');
        return;
      }
      if (codeLanguage === 'java' && !codeText.includes('class ') && !codeText.includes('public ')) {
        setValidationError('Java code should contain classes or public declarations');
        return;
      }
    }

    return {
      projectId: project.id,
      codeName: fileName.trim() || (file ? file.name : ''),
      fileName: fileName.trim() || (file ? file.name : ''),
      language: codeLanguage,
      version: version.trim(),
      codeText,
      file,
    };
  };

  const handleDiagramClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    console.log('🔵 handleDiagramClick called');
    const payload = buildPayload();
    console.log('🟢 Payload built:', payload);
    
    if (payload) {
      console.log('🟡 Calling onGenerateDiagram...');
      
      // If a file was uploaded but no code was typed, read the file content
      let codeTextToUse = payload.codeText;
      if (payload.file && !payload.codeText.trim()) {
        console.log('📖 Reading file content...');
        const fileContent = await payload.file.text();
        codeTextToUse = fileContent;
        console.log('✓ File content read:', fileContent.substring(0, 50) + '...');
      }
      
      // Call the handler with updated code text
      await onGenerateDiagram({
        ...payload,
        codeText: codeTextToUse
      });
      console.log('🟠 onGenerateDiagram finished');
    } else {
      console.log('🔴 Payload validation failed');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-lg" onClick={(e) => e.stopPropagation()}>
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

            <input
              id="file-name"
              type="text"
              className="code-upload-input"
              value={fileName}
              onChange={handleFileNameChange}
              placeholder={codeLanguage === 'python' ? 'payment_service.py' : 'StudentManager.java'}
              disabled={isProcessing || !!file}
            />
            <p className="code-upload-hint">
              <AlertCircle size={14} />
              If uploading a file, the name will be auto-filled. If pasting code, enter a name manually (must end with .py or .java).
            </p>

            <div className="code-upload-group">
              <label htmlFor="language" className="code-upload-label">
                <Code size={16} />
                {i18n.t('code.language.label')}
              </label>
              <div className="code-upload-select-wrapper">
                <select
                  id="language"
                  className="code-upload-select"
                  value={codeLanguage}
                  onChange={(e) => setCodeLanguage(e.target.value as 'python' | 'java')}
                  disabled={isProcessing}
                >
                  <option value="python">🐍 Python</option>
                  <option value="java">☕ Java</option>
                </select>
              </div>
            </div>

            <div className="code-upload-group">
              <label htmlFor="version" className="code-upload-label">
                <Settings size={16} />
                {i18n.t('code.version.label')}
              </label>
              <input
                id="version"
                type="text"
                className="code-upload-input"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder={t('code.version_placeholder')}
                disabled={isProcessing}
              />
            </div>

            <div className="code-upload-group full-width">
              <label htmlFor="code-text" className="code-upload-label">
                <FileText size={16} />
                {t('code.code_label')}
              </label>
              <div style={{ position: 'relative' }}>
                <textarea
                  id="code-text"
                  className="code-upload-textarea"
                  value={codeText}
                  onChange={handleCodeTextChange}
                  placeholder={t('code.code_placeholder')}
                  rows={10}
                  disabled={isProcessing}
                  maxLength={50000}
                />
                <div className={`char-counter ${codeText.length > 45000 ? 'warning' : ''} ${codeText.length > 49000 ? 'error' : ''}`}>
                  {codeText.length.toLocaleString()}/50,000
                </div>
              </div>
              <p className="code-upload-hint">
                <AlertCircle size={14} />
                {t('code.code_hint')}
              </p>
              {codeText.trim() && (
                <div className="form-feedback success">
                  <CheckCircle size={14} />
                  Code content provided ({codeText.split('\n').length} lines)
                </div>
              )}
            </div>

            <div className="code-upload-group full-width">
              <label htmlFor="code-file" className="code-upload-label">
                <Upload size={16} />
                {i18n.t('code.upload.label')}
              </label>
              <div className="code-upload-file-group">
                <input
                  id="code-file"
                  type="file"
                  className="code-upload-file-input"
                  accept={codeLanguage === 'python' ? '.py' : '.java'}
                  onChange={handleFileChange}
                  disabled={isProcessing}
                />
                <label
                  htmlFor="code-file"
                  className={`code-upload-file-label ${file ? 'code-upload-file-selected' : ''} ${dragOver ? 'drag-over' : ''}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <Upload size={48} className="code-upload-file-icon" />
                  <div className="code-upload-file-text">
                    {file ? (
                      <>
                        <CheckCircle size={20} style={{ marginRight: '8px', color: '#28a745' }} />
                        {file.name}
                      </>
                    ) : (
                      <>
                        📁 {i18n.t('code.upload.drag_drop')}
                      </>
                    )}
                  </div>
                  <div className="code-upload-file-subtext">
                    {codeLanguage === 'python' ? '🐍 Python files (.py)' : '☕ Java files (.java)'} • Max 10MB
                    {file && (
                      <span style={{ marginLeft: '8px', color: '#28a745' }}>
                        ✓ Valid file selected
                      </span>
                    )}
                  </div>
                </label>
              </div>
            </div>

            <div className="code-upload-actions">
              <button
                type="button"
                onClick={handleDiagramClick}
                disabled={isProcessing}
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
                    Generate Document
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
  );
};

export default CodeUploadForm;


