import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  BookOpen,
  Download,
  Edit3,
  Save,
  FileDown,
  Globe,
  Lightbulb,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  Sun,
  Moon
} from 'lucide-react';
import { API_ENDPOINTS } from './config/api.config';
import UnifiedApiService from './services/unifiedApiService';
import { extractMermaidCode } from './utils/jsonToMermaid ';
import { i18n } from './utils/i18n';
import { useAuth } from './context/AuthContext';
import { useLanguage } from './context/LanguageContext';
import NotificationBell from './compoents/NotificationBell';
import { sendNotification } from './utils/notificationHelper';
import './DocumentGenerationPage.css';

// Error Boundary Component
class DiagramErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Diagram Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="diagram-error-boundary">
          <div className="error-icon">
            <AlertTriangle size={48} color="#e74c3c" />
          </div>
          <h3>Diagram Error</h3>
          <p>Failed to render the diagram.</p>
          <details>
            <summary>Error Details</summary>
            <pre>{this.state.error?.message}</pre>
          </details>
          <button
            onClick={() => window.location.reload()}
            className="btn-retry"
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

interface LocationState {
  projectId: string;
  codeName: string;
  fileName: string;
  language: 'python' | 'java';
  codeText: string;
}

interface AnalysisResult {
  status: string;
  error_message?: string;
  class_diagram_data?: Record<string, unknown>;
  id: string;
  code_file_id?: string;
  analysis_completed_at?: string;
}

const DocumentGenerationPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState;
  const { user, isLoggedIn } = useAuth();
  const { language, setLanguage } = useLanguage();

  // Check if user is authenticated
  useEffect(() => {
    if (!isLoggedIn || !user) {
      console.log('🔐 User not authenticated, redirecting to signup...');
      navigate('/signup');
      return;
    }
  }, [isLoggedIn, user, navigate]);

  const [isDarkMode, setIsDarkMode] = useState(true);
  const diagramRef = useRef<HTMLDivElement>(null);
  const hasInitializedRef = useRef(false);  // 👈 منع الاستدعاء المزدوج من StrictMode
  const hasLoadedRef = useRef(false);  // 👈 منع الاستدعاء المزدوج لـ auto-load

  // Apply dark mode class to body
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [isDarkMode]);

  // States for toggles
  const [explanationLevel, setExplanationLevel] = useState<'high' | 'low'>('high');
  const [documentFormat, setDocumentFormat] = useState<'markdown' | 'pdf'>('markdown');

  // States for diagram
  const [classDiagram, setClassDiagram] = useState<string>('');
  const [isEditingDiagram, setIsEditingDiagram] = useState(false);
  const [editedDiagram, setEditedDiagram] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const saveTimeoutRef = useRef<number | null>(null);
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);
  const [diagramError, setDiagramError] = useState<string | null>(null);
  const [explanationError, setExplanationError] = useState<string | null>(null);

  // States for zoom and pan
  // Debug state for effect
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // State for analysis results
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult | null>(null);

  // States for loading and processing
  const [isGeneratingDiagram, setIsGeneratingDiagram] = useState(false);
  const [isGeneratingExplanation, setIsGeneratingExplanation] = useState(false);
  const [isGeneratingDocument, setIsGeneratingDocument] = useState(false);

  // Add ref to track ongoing requests
  const isGeneratingRef = useRef({
    diagram: false,
    explanation: false,
    document: false
  });

  // States for content
  const [codeExplanation, setCodeExplanation] = useState<string>('');
  const [generatedDocument, setGeneratedDocument] = useState<string>('');


  // 🔍 Debug: Check if we received the state
  console.log('📄 DocumentGenerationPage loaded with state:', state);

  // Check if state is missing and redirect to dashboard
  useEffect(() => {
    if (!state || !state.projectId || !state.codeText) {
      console.error('❌ Missing required state data:', state);
      navigate('/dashboard');
      return;
    }
  }, [state, navigate]);

  // Early return if state is not available yet
  if (!state || !state.projectId || !state.codeText) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '20px',
        padding: '20px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '24px', marginBottom: '10px' }}>
          ⚠️ Access Error
        </div>
        <div style={{ fontSize: '18px', marginBottom: '20px' }}>
          Please access this page through the project dashboard
        </div>
        <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '30px' }}>
          This page requires code data to be uploaded first
        </div>
        <button
          onClick={() => navigate('/dashboard')}
          style={{
            padding: '12px 24px',
            background: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Go to Dashboard
        </button>
      </div>
    );
  }
  // Zoom and Pan functions
  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.2, 0.5));
  };

  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 1 || (e.button === 0 && e.ctrlKey)) {
      e.preventDefault();
      setIsDragging(true);
      setDragStart({
        x: e.clientX - pan.x,
        y: e.clientY - pan.y
      });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(prev => Math.max(0.5, Math.min(3, prev * zoomFactor)));
  }, []);

  // Download functions
  const downloadPNG = useCallback(() => {
    if (!diagramRef.current) return;

    const svgElement = diagramRef.current.querySelector('svg');
    if (!svgElement) {
      alert('No diagram found to download.');
      return;
    }

    try {
      const clonedSvg = svgElement.cloneNode(true) as SVGElement;

      const bbox = svgElement.getBBox();
      const width = bbox.width || parseInt(svgElement.getAttribute('width') || '800');
      const height = bbox.height || parseInt(svgElement.getAttribute('height') || '600');

      clonedSvg.setAttribute('width', width.toString());
      clonedSvg.setAttribute('height', height.toString());
      clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      clonedSvg.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');

      const svgString = new XMLSerializer().serializeToString(clonedSvg);
      const encodedSvg = encodeURIComponent(svgString).replace(/'/g, '%27').replace(/"/g, '%22');
      const dataUrl = `data:image/svg+xml;charset=utf-8,${encodedSvg}`;

      const img = new Image();
      img.crossOrigin = 'anonymous';

      img.onload = () => {
        try {
          const canvas = document.createElement('canvas');
          const scale = 3;
          canvas.width = width * scale;
          canvas.height = height * scale;

          const ctx = canvas.getContext('2d', { alpha: false });
          if (!ctx) throw new Error('Could not get canvas context');

          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';

          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, canvas.width, canvas.height);

          ctx.scale(scale, scale);
          ctx.drawImage(img, 0, 0, width, height);

          canvas.toBlob(
            (blob) => {
              if (blob) {
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.download = `${state.fileName || 'diagram'}-class-diagram-${Date.now()}.png`;
                link.href = url;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                setTimeout(() => URL.revokeObjectURL(url), 100);
              } else {
                throw new Error('Failed to create PNG blob');
              }
            },
            'image/png',
            1.0
          );
        } catch (error) {
          console.error('Error converting to PNG:', error);
          alert('Failed to convert to PNG. Please try downloading as SVG instead.');
        }
      };

      img.onerror = (error) => {
        console.error('Error loading SVG image:', error);
        alert('Failed to load diagram for PNG conversion. Please try downloading as SVG instead.');
      };

      img.src = dataUrl;

    } catch (error) {
      console.error('Error in downloadPNG:', error);
      alert('Failed to download PNG. Please try downloading as SVG instead.');
    }
  }, [state.fileName]);


  const downloadSVG = useCallback(() => {
    if (!diagramRef.current) return;

    const svgElement = diagramRef.current.querySelector('svg');
    if (!svgElement) return;

    const svgString = new XMLSerializer().serializeToString(svgElement);
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const link = document.createElement('a');
    link.download = `${state.fileName || 'diagram'}-class-diagram.svg`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
    setShowDownloadMenu(false);
  }, [state.fileName]);

  // Helper function to get auth headers
  const getAuthHeaders = useCallback((url?: string) => {
    const token = localStorage.getItem('access_token');
    console.log('🔑 Checking authentication token:', {
      hasToken: !!token,
      tokenPreview: token ? `${token.substring(0, 20)}...` : 'none',
      url: url,
      isAiEndpoint: url?.includes('/api/analysis/ai-explanations/'),
      isAiGeneralEndpoint: url?.includes('/api/analysis/')
    });

    if (!token) {
      console.error('❌ No access token found in localStorage');
      navigate('/auth');
      return undefined;
    }

    const getCookie = (name: string) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) {
        return parts.pop()?.split(';').shift();
      }
      return null;
    };
    const csrfToken = getCookie('ai_csrftoken');
    const isUpmEndpoint = url?.includes('/api/upm/');
    const isAiEndpoint = url?.includes('/api/analysis/');
    const isAiExplanationEndpoint = url?.includes('/api/analysis/ai-explanations/');

    // Always add Authorization for AI endpoints, especially AI explanation endpoints
    const headers = {
      'Content-Type': 'application/json',
      ...(csrfToken && { 'X-CSRFToken': csrfToken }),
      ...(isUpmEndpoint && { 'Authorization': `Bearer ${token}` }),
      ...((isAiEndpoint || isAiExplanationEndpoint) && { 'Authorization': `Bearer ${token}` })
    };

    console.log('📤 Generated auth headers:', headers);
    console.log('🔑 Added Authorization header for AI endpoint:', url);
    return headers;
  }, [navigate]);

  // Helper function to save artifact to backend
  const saveArtifact = async (fileId: string, artifactType: 'class_diagram' | 'explanation' | 'document', content: string, metadata?: any) => {
    try {
      console.log(`🔄 Saving ${artifactType} artifact for file:`, fileId);
      console.log(`📊 Project ID: ${state.projectId}, Artifact Type: ${artifactType}`);

      // Use FormData for file upload
      const formData = new FormData();
      formData.append('file', new Blob([content], { type: 'text/plain' }), `${artifactType}.txt`);
      formData.append('project_id', state.projectId);
      formData.append('file_id', fileId);
      formData.append('artifact_type', artifactType);
      formData.append('metadata', JSON.stringify(metadata || {}));

      console.log(`🌐 Using UnifiedApiService to save artifact`);
      console.log(`📦 Request Data:`, formData);

      const response = await UnifiedApiService.saveArtifact(formData);
      console.log('✅ Artifact saved successfully:', response);
      return response.id || response._id;

    } catch (error: any) {
      console.error('❌ Failed to save artifact:', error);

      // Check if it's a 404 error
      if (error.response?.status === 404) {
        console.log('⚠️ Artifacts endpoint not found (404) - this endpoint needs to be implemented in Django backend');
        console.log('🔄 Continuing without saving artifact to backend - diagram will still work');

        // Just emit event for UI update and continue
        window.dispatchEvent(new CustomEvent('documentGenerated', {
          detail: { type: artifactType, projectId: state.projectId, content }
        }));
        return 'memory-only';
      } else if (error.response?.status === 409) {
        console.log('Artifact already exists, attempting to update...');

        try {
          const existingArtifacts = await UnifiedApiService.getProjectArtifacts(state.projectId, {
            file_id: fileId,
            artifact_type: artifactType
          });

          const existingArtifact = existingArtifacts.results?.[0] || existingArtifacts[0];

          if (existingArtifact?.id) {
            await UnifiedApiService.updateArtifact(existingArtifact.id, {
              content: content,
              metadata: metadata || {}
            });

            console.log('✅ Artifact updated successfully!');
            return existingArtifact.id;
          }
        } catch (updateError) {
          console.error('❌ Failed to update artifact:', updateError);
        }
      }

    }
  };

  // Helper function to get or create code file with conflict handling
  const getOrCreateCodeFile = async (codeFileData: any) => {
    try {
      console.log('Creating code file in AI service:', codeFileData);
      const codeFileEndpoint = API_ENDPOINTS.analysis.codefiles();
      console.log('API Endpoint:', codeFileEndpoint);

      const codeFileResponse = await fetch(codeFileEndpoint, {
        method: 'POST',
        headers: getAuthHeaders(codeFileEndpoint),
        credentials: 'include',
        body: JSON.stringify(codeFileData)
      });

      if (codeFileResponse.status === 409) {
        // 409 Conflict - file already exists, try to get existing file
        console.log('Code file already exists, fetching existing file...');

        // Try to find existing file by project and filename
        const existingFilesResponse = await fetch(API_ENDPOINTS.analysis.codefilesByProject(state.projectId), {
          headers: getAuthHeaders(API_ENDPOINTS.analysis.codefilesByProject(state.projectId)),
          credentials: 'include'
        });

        if (existingFilesResponse.ok) {
          const existingFiles = await existingFilesResponse.json();
          const existingFile = existingFiles.results?.find((file: any) =>
            file.filename === codeFileData.filename ||
            file.content === codeFileData.content
          ) || existingFiles.find((file: any) =>
            file.filename === codeFileData.filename ||
            file.content === codeFileData.content
          );

          if (existingFile) {
            console.log('Using existing code file:', existingFile.id);
            return existingFile.id;
          }
        }
        throw new Error('File exists but could not be retrieved');
      }

      if (!codeFileResponse.ok) {
        throw new Error(`Failed to create code file: ${codeFileResponse.status}`);
      }

      const codeFileResult = await codeFileResponse.json();
      const codeFileId = codeFileResult.id;

      if (codeFileResponse.status === 200) {
        console.log('Using existing file:', codeFileId);
      } else {
        console.log('New code file created:', codeFileId);
      }

      return codeFileId;
    } catch (error) {
      console.error('Error creating/getting code file:', error);
      throw error;
    }
  };

  const getLatestAnalysisResult = useCallback(async (): Promise<AnalysisResult | null> => {
    try {
      const apiUrl = API_ENDPOINTS.analysis.results();
      console.log('🔍 [DEBUG] Fetching analysis results from:', apiUrl);

      const response = await fetch(apiUrl, {
        headers: getAuthHeaders(apiUrl),
        credentials: 'include'
      });

      console.log('📡 [DEBUG] Response status:', response.status);
      console.log('📡 [DEBUG] Response URL:', response.url);

      if (response.ok) {
        const data = await response.json();
        console.log('📊 [DEBUG] Analysis results data:', data);

        if (data.results && data.results.length > 0) {
          console.log('✅ [DEBUG] Found', data.results.length, 'results');
          const latestResult = data.results.sort((a: AnalysisResult, b: AnalysisResult) =>
            new Date(b.analysis_completed_at || 0).getTime() - new Date(a.analysis_completed_at || 0).getTime()
          )[0];
          console.log('🎯 [DEBUG] Latest result found:', latestResult.id);
          return latestResult;
        } else {
          console.log('ℹ️ [DEBUG] No analysis results found');
          return null;
        }
      } else {
        console.error('❌ [DEBUG] Failed to fetch analysis results:', response.status, response.statusText);

        // Enhanced error handling for specific status codes
        if (response.status === 404) {
          console.error('🔍 [DEBUG] Analysis results endpoint not found - check API configuration');
          console.error('🔍 [DEBUG] Expected endpoint: /api/analysis/analysis-results/');
          console.error('🔍 [DEBUG] Actual URL called:', apiUrl);
        } else if (response.status === 401) {
          console.error('🔐 [DEBUG] Authentication failed - check token validity');
        } else if (response.status === 403) {
          console.error('🚫 [DEBUG] Authorization failed - check permissions');
        }

        const errorText = await response.text();
        console.error('❌ [DEBUG] Error response body:', errorText);
        return null;
      }
    } catch (error) {
      console.error('❌ [DEBUG] Error in getLatestAnalysisResult:', error);
      return null;
    }
  }, []);

  // Render diagram function
  const renderDiagram = useCallback(async (codeToRender: string) => {
    console.log('🎬 renderDiagram called with code length:', codeToRender?.length);
    if (!codeToRender) {
      console.warn('⚠️ codeToRender is empty or null');
      return;
    }
    if (!diagramRef.current) {
      console.warn('⚠️ diagramRef.current is null');
      return;
    }

    try {
      console.log('📦 Importing mermaid...');
      const mermaidInstance = await import('mermaid');
      console.log('✅ Mermaid imported successfully');

      // Force re-initialize if needed
      console.log('⚙️ Initializing mermaid with config...');
      mermaidInstance.default.initialize({
        theme: 'base',
        securityLevel: 'loose',
        fontFamily: 'Arial, sans-serif',
        fontSize: 14
      } as any);

      // Remove old SVG to avoid overlap
      if (diagramRef.current) {
        diagramRef.current.innerHTML = '';
        console.log('🧹 Cleared previous innerHTML');
      }

      // Generate unique ID for this diagram
      const diagramId = `diagram-${Date.now()}`;
      console.log('🔑 Generated diagram ID:', diagramId);
      console.log('📝 Code to render:\n', codeToRender);

      // Render the diagram
      console.log('🎨 Calling mermaid.render()...');
      const { svg } = await mermaidInstance.default.render(diagramId, codeToRender);
      console.log('✅ Mermaid render succeeded! SVG length:', svg?.length);
      console.log('📊 First 100 chars of SVG:', svg?.substring(0, 100));

      if (diagramRef.current) {
        diagramRef.current.innerHTML = svg;
        console.log('✅ SVG inserted into diagramRef.current');
        console.log('🔍 diagramRef.current innerHTML length:', diagramRef.current.innerHTML.length);
      } else {
        console.error('❌ diagramRef.current became null after render');
      }

      setDiagramError(null);
    } catch (error) {
      console.error('❌ Mermaid render ERROR:', error);
      console.error('Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : 'No stack',
        error: String(error)
      });
      const errorMessage = error instanceof Error ? error.message : 'Failed to render diagram';
      setDiagramError(errorMessage);
      if (diagramRef.current) {
        diagramRef.current.innerHTML = `
          <div class="diagram-error">
            <p>❌ Error rendering diagram:</p>
            <pre>${errorMessage}</pre>
            <p>Code:</p>
            <pre>${codeToRender}</pre>
          </div>
        `;
      }
    }
  }, [setDiagramError]);

  // Render diagram when classDiagram changes
  useEffect(() => {
    if (classDiagram && diagramRef.current && !isEditingDiagram) {
      const timeoutId = setTimeout(() => {
        console.log('🎨 Rendering diagram from classDiagram state:', classDiagram.substring(0, 100));
        renderDiagram(classDiagram);
      }, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [classDiagram, isEditingDiagram, renderDiagram, analysisResults, state.fileName]);

  // Render diagram when editedDiagram changes (during editing)
  useEffect(() => {
    if (editedDiagram && diagramRef.current && isEditingDiagram) {
      const timeoutId = setTimeout(() => {
        console.log('✏️ Rendering edited diagram:', editedDiagram.substring(0, 100));
        renderDiagram(editedDiagram);
      }, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [editedDiagram, isEditingDiagram, renderDiagram]);

  // Add wheel event listener for zoom
  useEffect(() => {
    const diagramElement = diagramRef.current;
    if (diagramElement && !isEditingDiagram) {
      diagramElement.addEventListener('wheel', handleWheel, { passive: false });
      return () => {
        diagramElement.removeEventListener('wheel', handleWheel);
      };
    }
  }, [handleWheel, isEditingDiagram]);

  const generateClassDiagram = async () => {
    // Prevent duplicate requests
    if (isGeneratingRef.current.diagram || isGeneratingDiagram) {
      console.log('⚠️ Class diagram generation already in progress, skipping...');
      return;
    }

    console.log('🚀 Starting class diagram generation...');
    console.log('📋 State:', {
      fileName: state.fileName,
      projectId: state.projectId,
      language: state.language,
      codeTextLength: state.codeText?.length
    });

    setIsGeneratingDiagram(true);
    isGeneratingRef.current.diagram = true;
    setDiagramError(null); // Clear previous errors
    try {
      const codeFileData = {
        filename: state.fileName || `uploaded_code.${state.language === 'java' ? 'java' : 'py'}`,
        file_type: state.language,
        content: state.codeText,
        source_project_id: state.projectId
      };

      // Use new conflict-handling function
      const codeFileId = await getOrCreateCodeFile(codeFileData);
      console.log('📄 Code file ID:', codeFileId);

      // Request analysis using UnifiedApiService
      const analysisData = {
        code_file_id: codeFileId,
        analysis_type: 'class_diagram'
      };

      console.log('📤 Requesting analysis:', analysisData);

      const analysisResult = await UnifiedApiService.generateClassDiagram(codeFileId, state.projectId);
      console.log('📊 Analysis initiated:', analysisResult);

      // Poll for results
      const taskId = analysisResult.task_id;
      const maxAttempts = 30;
      const pollInterval = 2000;
      let attempts = 0;

      const pollForResult = async (): Promise<void> => {
        while (attempts < maxAttempts) {
          attempts++;
          console.log(`🔄 Polling attempt ${attempts}/${maxAttempts} for code file ${codeFileId}...`);

          // Query analysis results by task_id using UnifiedApiService
          console.log('🔗 Polling for results with task_id:', taskId);

          const resultsData = await UnifiedApiService.getAnalysisResults(codeFileId);
          console.log('📊 Analysis results:', resultsData);

          // Check if we have results
          if (resultsData.results && resultsData.results.length > 0) {
            // Get the latest result
            const latestResult = resultsData.results[0];
            console.log('✅ Class diagram generated successfully!');
            console.log('📊 Analysis result:', latestResult);

            // Set analysis results state
            setAnalysisResults(latestResult);

            // Emit event to refresh documents list
            window.dispatchEvent(new CustomEvent('documentGenerated', {
              detail: { type: 'class_diagram', projectId: state.projectId }
            }));

            // Send notification for class diagram generation
            await sendNotification(user, 'documentation', 'generated', {
              fileName: `${state.fileName || 'diagram'}-class-diagram`,
              fileType: 'diagram'
            });

            if (latestResult.status === 'COMPLETED' || latestResult.status === 'completed') {
              console.log('✅ Analysis completed!');
              console.log('📊 Has class_diagram_data:', !!latestResult.class_diagram_data);

              if (latestResult.class_diagram_data) {
                console.log('📊 Class diagram data:', latestResult.class_diagram_data);

                try {
                  // استخدام دالة extractMermaidCode لتحويل JSON إلى Mermaid
                  const mermaidCode = extractMermaidCode(latestResult.class_diagram_data);
                  console.log('� Extracted Mermaid code:', mermaidCode);

                  // Auto-save the class diagram (with error handling)
                  try {
                    await saveArtifact(codeFileId, 'class_diagram', mermaidCode, {
                      format: 'mermaid',
                      generated_at: new Date().toISOString(),
                      analysis_id: latestResult.id
                    });
                  } catch (saveError: any) {
                    console.warn('⚠️ Failed to save artifact:', saveError.message);
                    // Continue even if save fails - still emit event for UI
                  }

                  setClassDiagram(mermaidCode);
                  console.log('New Mermaid code extracted:', mermaidCode);  // Log to see if new
                  // Set editedDiagram to match for consistency
                  setEditedDiagram(mermaidCode);

                  // Render the diagram
                  console.log('🚀 About to renderDiagram with mermaidCode length:', mermaidCode.length);
                  console.log('🚀 Mermaid code content:', mermaidCode);
                  await renderDiagram(mermaidCode);
                  console.log('✅ Class diagram rendered successfully!');
                  setDiagramError(null); // Clear any previous errors
                  return;
                } catch (mermaidError) {
                  console.error('❌ Mermaid extraction error:', mermaidError);
                  const errorMsg = mermaidError instanceof Error ? mermaidError.message : 'Failed to convert diagram data to Mermaid format';

                  // Check if the data has classes
                  const hasClasses = latestResult.class_diagram_data?.classes &&
                    Array.isArray(latestResult.class_diagram_data.classes) &&
                    latestResult.class_diagram_data.classes.length > 0;

                  if (!hasClasses) {
                    throw new Error('No classes found in the code. Please make sure your code contains valid class definitions.');
                  }

                  // Save raw data if Mermaid extraction fails
                  try {
                    await saveArtifact(codeFileId, 'class_diagram', JSON.stringify(latestResult.class_diagram_data), {
                      format: 'raw_json',
                      generated_at: new Date().toISOString(),
                      analysis_id: latestResult.id,
                      error: 'Mermaid extraction failed'
                    });
                  } catch (saveErr) {
                    console.warn('Failed to save raw data:', saveErr);
                  }

                  setClassDiagram(JSON.stringify(latestResult.class_diagram_data, null, 2));
                  setEditedDiagram(JSON.stringify(latestResult.class_diagram_data, null, 2));

                  // Try to render as text if Mermaid fails
                  if (diagramRef.current) {
                    diagramRef.current.innerHTML = `
                      <div class="diagram-error" style="padding: 20px; text-align: center;">
                        <p style="color: #c53030; margin-bottom: 12px;"><strong>Error converting diagram:</strong></p>
                        <p style="color: #718096; font-size: 0.9rem;">${errorMsg}</p>
                        <p style="color: #718096; font-size: 0.85rem; margin-top: 12px;">Raw data saved. You can edit it manually.</p>
                      </div>
                    `;
                  }
                  return;
                }
              } else {
                console.warn('⚠️ No class_diagram_data in result. Result keys:', Object.keys(latestResult));
                throw new Error('Analysis completed but no class diagram data was generated. The code may not contain valid class definitions.');
              }
            } else if (latestResult.status === 'failed') {
              throw new Error(`Analysis failed: ${latestResult.error_message || 'Unknown error'}`);
            } else if (latestResult.status === 'pending' || latestResult.status === 'processing' || latestResult.status === 'IN_PROGRESS') {
              if (attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, pollInterval));
                return pollForResult();
              } else {
                throw new Error('Analysis timeout');
              }
            }
          }

          // Wait before next poll
          await new Promise(resolve => setTimeout(resolve, pollInterval));
        }

        throw new Error('Diagram generation timeout');
      };

      await pollForResult();

    } catch (error) {
      console.error('❌ Error generating class diagram:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

      // Show user-friendly error message
      const userMessage = errorMessage.includes('timeout')
        ? 'Class diagram generation is taking too long. Please try again or check if the code contains valid class definitions.'
        : errorMessage.includes('failed') || errorMessage.includes('Failed')
          ? `Failed to generate class diagram: ${errorMessage}. Please check your code and try again.`
          : `Error: ${errorMessage}`;

      alert(userMessage);

      // Set error state for UI
      setDiagramError(userMessage);
    } finally {
      setIsGeneratingDiagram(false);
      isGeneratingRef.current.diagram = false;
    }
  };

  const generateCodeExplanation = async () => {
    // Check if user is authenticated
    if (!isLoggedIn || !user) {
      console.error('❌ User not authenticated for explanation generation');
      setExplanationError('Please login first to generate explanations');
      navigate('/signup');
      return;
    }

    // Prevent duplicate requests
    if (isGeneratingRef.current.explanation || isGeneratingExplanation) {
      console.log('⚠️ Code explanation generation already in progress, skipping...');
      return;
    }

    setIsGeneratingExplanation(true);
    isGeneratingRef.current.explanation = true;
    setExplanationError(null); // Clear previous errors
    try {
      console.log('🚀 Generating code explanation...');

      // Try to get the latest analysis result first
      const latestResult = await getLatestAnalysisResult();

      let codeFileId: string;

      if (latestResult && latestResult.code_file_id) {
        console.log('✅ Using existing code file ID from latest analysis:', latestResult.code_file_id);
        codeFileId = latestResult.code_file_id;
      } else {
        // Create a new code file if no existing one found
        console.log('📤 Creating new code file for explanation...');
        const codeFileData = {
          filename: state.fileName || `uploaded_code.${state.language === 'java' ? 'java' : 'py'}`,
          file_type: state.language,
          content: state.codeText,
          source_project_id: state.projectId
        };

        const codeFileResponse = await fetch(API_ENDPOINTS.analysis.codefiles(), {
          method: 'POST',
          headers: getAuthHeaders(API_ENDPOINTS.analysis.codefiles()),
          credentials: 'include',
          body: JSON.stringify(codeFileData)
        });

        if (!codeFileResponse.ok) {
          throw new Error(`Failed to create code file: ${codeFileResponse.status}`);
        }

        const codeFileResult = await codeFileResponse.json();
        codeFileId = codeFileResult.id;
        if (codeFileResponse.status === 200) {
          console.log('⚠️ Using existing file for explanation:', codeFileId);
        } else {
          console.log('✅ New code file created for explanation:', codeFileId);
        }
      }

      // Now request AI explanation using the correct endpoint
      console.log('📤 Requesting AI explanation with analysis_id:', latestResult?.id, 'code_file_id:', codeFileId, 'exp_type:', explanationLevel);

      // If we don't have a latest analysis result, we need to create one first
      let analysisId = latestResult?.id;
      if (!analysisId) {
        console.log('📤 No existing analysis found, creating basic analysis for AI explanation...');
        const analysisData = {
          code_file_id: codeFileId,
          analysis_type: 'class_diagram' // Create basic analysis first
        };

        const analysisResponse = await fetch(API_ENDPOINTS.analysis.analyze(), {
          method: 'POST',
          headers: getAuthHeaders(API_ENDPOINTS.analysis.analyze()),
          credentials: 'include',
          body: JSON.stringify(analysisData)
        });

        if (!analysisResponse.ok) {
          throw new Error(`Basic analysis creation failed: ${analysisResponse.status}`);
        }

        const analysisResult = await analysisResponse.json();
        analysisId = analysisResult.id;
        console.log('✅ Basic analysis created for AI explanation:', analysisId);
      }

      const aiExplanationResponse = await UnifiedApiService.generateAIExplanation(
        analysisId!, // We know it exists because we throw error if it doesn't
        explanationLevel
      );

      console.log('🆔 AI Explanation task started:', aiExplanationResponse);
      const taskId = aiExplanationResponse.task_id;

      if (!taskId) {
        throw new Error('No task ID received from AI explanation response');
      }

      // Poll for results
      let attempts = 0;
      const maxAttempts = 60;
      const pollInterval = 2000;

      // Small delay before starting polling to allow backend to save the task
      await new Promise(resolve => setTimeout(resolve, 1000));

      const pollForResult = async (): Promise<any> => {
        attempts++;
        console.log(`🔄 Polling for AI explanation ${attempts}/${maxAttempts}...`);

        // Use the AI explanation task status endpoint
        console.log('🔗 Checking AI explanation task status for:', taskId);

        const taskStatus = await UnifiedApiService.getExplanationTaskStatus(taskId);
        console.log('📊 AI explanation task status:', taskStatus);

        // Check if the task is completed
        if (taskStatus.status === 'completed' || taskStatus.status === 'COMPLETED') {
          console.log('✅ AI explanation completed!');

          // Get the explanation text from the task result
          let explanationText = '';

          if (taskStatus.result && taskStatus.result.explanation_text) {
            explanationText = taskStatus.result.explanation_text;
          } else if (taskStatus.result && typeof taskStatus.result === 'string') {
            explanationText = taskStatus.result;
          } else if (taskStatus.result) {
            explanationText = JSON.stringify(taskStatus.result, null, 2);
          }

          // Debug if still empty
          if (!explanationText) {
            console.warn('⚠️ No explanation text found in task result. Available fields:', Object.keys(taskStatus.result || {}));
            explanationText = `AI explanation completed but no text found. Task result keys: ${Object.keys(taskStatus.result || {}).join(', ')}`;
          }

          setCodeExplanation(explanationText);
          console.log('✅ AI explanation set successfully!');

          // Send notification for explanation generation
          await sendNotification(user, 'explanation', 'generated', {
            fileName: state.fileName,
            explanationLevel: explanationLevel === 'high' ? 'High Level' : 'Low Level'
          });

          // Emit event to refresh documents list
          window.dispatchEvent(new CustomEvent('documentGenerated', {
            detail: { type: 'explanation', projectId: state.projectId }
          }));
          return taskStatus;
        } else if (taskStatus.status === 'failed' || taskStatus.status === 'FAILURE') {
          throw new Error(`AI explanation failed: ${taskStatus.error || 'Unknown error'}`);
        }
        // Task is still processing (pending, processing, etc.)
        else if (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, pollInterval));
          return pollForResult();
        } else {
          throw new Error('AI explanation timeout');
        }
      };

      await pollForResult();

    } catch (error: any) {
      console.error('❌ Error generating explanation:', error);

      // Handle different error types with specific messages
      let errorMessage = 'Unknown error occurred';

      if (error.response) {
        const status = error.response.status;

        if (status === 401) {
          errorMessage = 'Authentication required. Please login to generate explanations.';
          // Redirect to login page
          navigate('/signup');
        } else if (status === 404) {
          errorMessage = 'AI explanation service not found. Please check if the backend is running.';
        } else if (status === 400) {
          errorMessage = 'Invalid request. Please make sure you have completed code analysis first.';
        } else if (status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else {
          errorMessage = `Request failed with status code ${status}.`;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      // Show user-friendly error message
      if (errorMessage.includes('timeout')) {
        errorMessage = 'Explanation generation is taking too long. Please try again.';
      } else if (errorMessage.includes('Authentication')) {
        errorMessage = 'Please login first to generate explanations.';
      }

      setExplanationError(errorMessage);
      alert(errorMessage); // Show popup for immediate feedback
    } finally {
      setIsGeneratingExplanation(false);
      isGeneratingRef.current.explanation = false;
    }
  };

  const generateDocument = async (action: 'display' | 'download') => {
    // Prevent duplicate requests
    if (isGeneratingRef.current.document || isGeneratingDocument) {
      console.log('⚠️ Document generation already in progress, skipping...');
      return;
    }

    setIsGeneratingDocument(true);
    isGeneratingRef.current.document = true;
    try {
      console.log('🚀 Generating document...');

      // Get the latest analysis result to find the code file
      const latestResult = await getLatestAnalysisResult();

      if (!latestResult || !latestResult.id) {
        throw new Error('No analysis found. Please generate a diagram first.');
      }

      const documentData = {
        code_file_id: latestResult.id,
        document_format: documentFormat,
        include_diagram: true,
        include_explanation: true,
        explanation_level: explanationLevel === 'high' ? 'high_level' : 'low_level',
        mode: action === 'download' ? 'download' : 'display'
      };

      console.log('📤 Requesting document generation:', documentData);

      const documentResponse = await fetch(API_ENDPOINTS.analysis.generateDocument(), {
        method: 'POST',
        headers: getAuthHeaders(API_ENDPOINTS.analysis.generateDocument()),
        credentials: 'include',
        body: JSON.stringify(documentData)
      });

      console.log('📡 Document response status:', documentResponse.status);
      console.log('📡 Document response headers:', [...documentResponse.headers.entries()]);

      if (!documentResponse.ok) {
        const errorText = await documentResponse.text();
        console.error('❌ Document generation failed:', errorText);
        throw new Error(`Document generation failed: ${documentResponse.status} - ${errorText}`);
      }

      if (action === 'download') {
        // Handle download
        console.log('📥 Starting download process...');
        console.log('📡 Response headers:', [...documentResponse.headers.entries()]);
        console.log('📡 Response status:', documentResponse.status);
        console.log('📡 Content-Type:', documentResponse.headers.get('content-type'));

        const blob = await documentResponse.blob();
        console.log('📦 Blob created:', blob);
        console.log('📦 Blob size:', blob.size);
        console.log('📦 Blob type:', blob.type);

        if (blob.size === 0) {
          throw new Error('Downloaded file is empty');
        }

        // Validate PDF content type
        if (documentFormat === 'pdf' && !blob.type.includes('pdf') && !blob.type.includes('application/octet-stream')) {
          console.warn('⚠️ Unexpected blob type for PDF:', blob.type);
        }

        // For PDF, validate first few bytes to ensure it's a valid PDF
        if (documentFormat === 'pdf') {
          const reader = new FileReader();
          reader.onloadend = () => {
            const arr = new Uint8Array(reader.result as ArrayBuffer);
            const header = String.fromCharCode.apply(null, Array.from(arr.slice(0, 4)));
            if (header !== '%PDF') {
              console.error('❌ Invalid PDF file header:', header);
              throw new Error('Downloaded file is not a valid PDF');
            }
          };
          reader.readAsArrayBuffer(blob.slice(0, 4));
        }

        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${state.fileName || 'document'}.${documentFormat === 'pdf' ? 'pdf' : 'md'}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        console.log('✅ Document downloaded successfully!');

        // Send notification for document download
        await sendNotification(user, 'document', 'downloaded', {
          fileName: `${state.fileName || 'document'}.${documentFormat === 'pdf' ? 'pdf' : 'md'}`,
          fileType: documentFormat === 'pdf' ? 'PDF' : 'Markdown'
        });

        // Emit event to refresh documents list
        window.dispatchEvent(new CustomEvent('documentGenerated', {
          detail: { type: 'document', projectId: state.projectId }
        }));
      } else {
        // Handle display
        const documentText = await documentResponse.text();
        setGeneratedDocument(documentText);
        console.log('✅ Document generated and displayed!');

        // Send notification for document generation
        await sendNotification(user, 'document', 'generated', {
          fileName: `${state.fileName || 'document'}.${documentFormat === 'pdf' ? 'pdf' : 'md'}`,
          fileType: documentFormat === 'pdf' ? 'PDF' : 'Markdown'
        });

        // Emit event to refresh documents list
        window.dispatchEvent(new CustomEvent('documentGenerated', {
          detail: { type: 'document', projectId: state.projectId }
        }));
      }

    } catch (error) {
      console.error('❌ Error generating document:', error);
      alert(`Failed to generate document: ${(error as Error).message}`);
    } finally {
      setIsGeneratingDocument(false);
      isGeneratingRef.current.document = false;
    }
  };

  const handleSaveDiagram = async () => {
    // Prevent double-click saves
    if (isSaving) {
      console.log('Save already in progress, ignoring click');
      return;
    }

    // Clear any existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    setIsSaving(true);

    try {
      setClassDiagram(editedDiagram);
      setIsEditingDiagram(false);
      // Trigger re-render
      await renderDiagram(editedDiagram);
    } catch (error) {
      console.error('Error saving diagram:', error);
    } finally {
      // Reset saving state after a delay
      saveTimeoutRef.current = window.setTimeout(() => {
        setIsSaving(false);
      }, 2000); // 2 second cooldown
    }
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // Generate initial class diagram
  useEffect(() => {
    // منع الاستدعاء المزدوج من React.StrictMode في development
    if (hasInitializedRef.current || isGeneratingRef.current.diagram) return;

    if (state?.codeText && state?.projectId) {
      hasInitializedRef.current = true;
      generateClassDiagram();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  useEffect(() => {
    const loadLatestAnalysis = async () => {
      if (hasLoadedRef.current) return;
      hasLoadedRef.current = true;

      try {
        const latestResult = await getLatestAnalysisResult();
        if (latestResult) {
          console.log('🎯 Page loaded - Latest analysis found:', latestResult.id);
          (window as unknown as Record<string, unknown>).latestAnalysisResult = latestResult;
        }
      } catch (error) {
        console.log('⚠️ Error checking for latest analysis:', error);
      }
    };
    loadLatestAnalysis();
  }, [getLatestAnalysisResult]);

  console.log('🎨 Rendering DocumentGenerationPage with state:', state);
  console.log('📊 Current states - isDarkMode:', isDarkMode, 'classDiagram:', classDiagram.substring(0, 50));

  return (
    <DiagramErrorBoundary>
      <div className={`premium-hero ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
        {/* Animated Background */}
        <div className="animated-bg">
          <div className="floating-particles">
            {[...Array(20)].map((_, i) => (
              <div
                key={i}
                className="particle"
                style={{
                  left: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 10}s`,
                  animationDuration: `${15 + Math.random() * 10}s`
                }}
              />
            ))}
          </div>
          <div className="geometric-lines">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="geo-line"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  transform: `rotate(${Math.random() * 360}deg)`,
                  animationDelay: `${Math.random() * 5}s`
                }}
              />
            ))}
          </div>
        </div>
        {/* Header */}
        <div className={`doc-gen-header backdrop-blur-md border-b ${isDarkMode
          ? 'bg-black/20 border-white/10'
          : 'bg-white/80 border-gray-200/50'
          }`}>
          <div className="header-left">
            <button onClick={() => navigate(-1)} className={`btn-back ${isDarkMode
              ? 'text-white hover:bg-white/10'
              : 'text-gray-700 hover:bg-gray-100'
              }`}>
              <ArrowLeft size={18} />
              {i18n.t('doc.back')}
            </button>
            <div className="user-info">
              <span className={`username ${isDarkMode ? 'text-white' : 'text-gray-800'
                }`}>{user?.username || 'Guest'}</span>
            </div>
          </div>

          <h1 className={`doc-gen-title ${isDarkMode ? 'text-white' : 'text-gray-800'
            }`}>
            <FileText size={24} />
            {state?.codeName || 'Document Generation'} - {state?.fileName || 'Untitled'}
          </h1>

          <div className="header-right">
            {user?.id && <NotificationBell userId={user?.id.toString()} />}
            <button
              className={`p-2 rounded-lg border transition-all duration-300 backdrop-blur-sm ${isDarkMode
                ? 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                : 'bg-gray-100/50 border-gray-200/50 text-gray-700 hover:bg-gray-200/50'
                }`}
              onClick={() => setIsDarkMode(!isDarkMode)}
              title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <button
              className={`px-3 py-1.5 rounded-full border text-sm font-medium transition-all duration-300 backdrop-blur-sm ${isDarkMode
                ? 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                : 'bg-purple-100/50 border-purple-200/50 text-purple-700 hover:bg-purple-200/50'
                }`}
              onClick={() => setLanguage(language === 'en' ? 'ar' : 'en')}
              title={language === 'en' ? 'Switch to Arabic' : 'التبديل للإنجليزية'}
            >
              <Globe size={18} />
              {language === 'en' ? i18n.t('lang.arabic') : i18n.t('lang.english')}
            </button>
          </div>
        </div>

        {/* Controls */}
        <div className={`doc-gen-controls backdrop-blur-sm border rounded-xl p-6 ${isDarkMode
          ? 'bg-black/20 border-white/10'
          : 'bg-white/70 border-gray-200/50'
          }`}>
          <div className="control-group">
            <label className="control-label">
              <Lightbulb size={16} />
              {i18n.t('doc.explanation.level')}
            </label>
            <div className="toggle-switch">
              <button
                className={`toggle-option ${explanationLevel === 'high' ? 'active' : ''}`}
                onClick={() => setExplanationLevel('high')}
              >
                {i18n.t('doc.high.level')}
              </button>
              <button
                className={`toggle-option ${explanationLevel === 'low' ? 'active' : ''}`}
                onClick={() => setExplanationLevel('low')}
              >
                {i18n.t('doc.low.level')}
              </button>
            </div>
          </div>

          <div className="control-group">
            <label className="control-label">
              <FileDown size={16} />
              {i18n.t('doc.document.format')}
            </label>
            <div className="toggle-switch">
              <button
                className={`toggle-option ${documentFormat === 'markdown' ? 'active' : ''}`}
                onClick={() => setDocumentFormat('markdown')}
              >
                {i18n.t('doc.markdown')}
              </button>
              <button
                className={`toggle-option ${documentFormat === 'pdf' ? 'active' : ''}`}
                onClick={() => setDocumentFormat('pdf')}
              >
                {i18n.t('doc.pdf')}
              </button>
            </div>
          </div>

          <div className="control-actions">
            <button
              onClick={generateCodeExplanation}
              disabled={isGeneratingExplanation}
              className="btn-generate"
            >
              <BookOpen size={18} />
              {isGeneratingExplanation ? i18n.t('doc.generating') : i18n.t('doc.generate.explanation')}
            </button>
            <button
              onClick={() => generateDocument('display')}
              disabled={isGeneratingDocument || !codeExplanation}
              className="btn-generate-doc"
            >
              <FileText size={18} />
              {isGeneratingDocument ? i18n.t('doc.creating.document') : i18n.t('doc.generate.document')}
            </button>
            <button
              onClick={() => generateDocument('download')}
              disabled={isGeneratingDocument || !codeExplanation}
              className="btn-download-doc"
            >
              <Download size={18} />
              {isGeneratingDocument ? i18n.t('doc.downloading') : i18n.t('doc.download.document')}
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="doc-gen-content pt-20">
          {/* Class Diagram Section */}
          <div className={`content-section diagram-section backdrop-blur-sm border rounded-xl p-8 mb-6 ${isDarkMode
            ? 'bg-black/20 border-white/10'
            : 'bg-white/70 border-gray-200/50'
            }`}>
            <div className={`section-header mb-6`}>
              <div className="section-title-wrapper">
                <h2 className={`section-title text-2xl font-bold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-800'
                  }`}>
                  <div className={`title-icon w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${isDarkMode
                    ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white'
                    : 'bg-gradient-to-br from-purple-600 to-pink-600 text-white'
                    }`}>
                    <FileText size={22} />
                  </div>
                  <span className={`title-text ${isDarkMode ? 'text-white' : 'text-gray-800'
                    }`}>{i18n.t('doc.class.diagram')}</span>
                  <div className={`status-badge auto-generated px-3 py-1 rounded-full text-xs font-medium ${isDarkMode
                    ? 'bg-purple-500/20 text-purple-200 border-purple-400/30'
                    : 'bg-purple-100/50 text-purple-700 border-purple-300/50'
                    }`}>
                    <span className="badge-dot w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                    {i18n.t('doc.auto.generated') || 'Auto-generated'}
                  </div>
                </h2>
                <p className={`section-description text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'
                  }`}>
                  {i18n.t('doc.diagram.description') || 'Interactive class diagram visualization with zoom and pan controls'}
                </p>
              </div>
              <div className="section-actions">
                {!isEditingDiagram ? (
                  <>
                    {!classDiagram && !isGeneratingDiagram && (
                      <button
                        onClick={() => {
                          setDiagramError(null);
                          generateClassDiagram();
                        }}
                        className="btn-generate"
                        style={{ marginRight: '8px' }}
                      >
                        <RefreshCw size={18} /> Generate Diagram
                      </button>
                    )}
                    <div style={{ position: 'relative' }}>
                      <button
                        onClick={() => setShowDownloadMenu(!showDownloadMenu)}
                        className="btn-download"
                        disabled={isGeneratingDiagram || !classDiagram}
                      >
                        <Download size={18} /> {i18n.t('doc.download')}
                      </button>
                      {showDownloadMenu && (
                        <div className="dropdown-menu" style={{
                          position: 'absolute',
                          top: '100%',
                          right: 0,
                          marginTop: '8px',
                          background: 'white',
                          border: '1px solid #ddd',
                          borderRadius: '8px',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                          zIndex: 1000,
                          minWidth: '150px'
                        }}>
                          <button
                            onClick={() => {
                              downloadSVG();
                              setShowDownloadMenu(false);
                            }}
                            className="dropdown-item"
                            style={{
                              width: '100%',
                              padding: '8px 12px',
                              border: 'none',
                              background: 'none',
                              textAlign: 'left',
                              cursor: 'pointer',
                              fontSize: '14px'
                            }}
                          >
                            {i18n.t('doc.download.svg')}
                          </button>
                          <button
                            onClick={() => {
                              downloadPNG();
                              setShowDownloadMenu(false);
                            }}
                            className="dropdown-item"
                            style={{
                              width: '100%',
                              padding: '8px 12px',
                              border: 'none',
                              background: 'none',
                              textAlign: 'left',
                              cursor: 'pointer',
                              fontSize: '14px'
                            }}
                          >
                            {i18n.t('doc.download.png')}
                          </button>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        setIsEditingDiagram(true);
                        setEditedDiagram(classDiagram);
                      }}
                      className="btn-edit"
                      disabled={isGeneratingDiagram || !classDiagram}
                    >
                      <Edit3 size={18} /> {i18n.t('doc.edit')}
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={handleSaveDiagram}
                      className="btn-save"
                      disabled={isSaving}
                    >
                      <Save size={18} /> {isSaving ? 'Saving...' : i18n.t('doc.save')}
                    </button>
                    <button
                      onClick={() => {
                        setIsEditingDiagram(false);
                        setEditedDiagram(classDiagram);
                      }}
                      className="btn-cancel"
                    >
                      {i18n.t('doc.cancel')}
                    </button>
                  </>
                )}
              </div>
            </div>

            {diagramError && (
              <div style={{
                background: '#fff5f5',
                border: '1px solid #fc8181',
                borderRadius: '8px',
                padding: '12px 16px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                color: '#c53030'
              }}>
                <AlertTriangle size={20} />
                <div>
                  <strong>Error generating class diagram:</strong>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.9rem' }}>{diagramError}</p>
                  <button
                    onClick={() => {
                      setDiagramError(null);
                      generateClassDiagram();
                    }}
                    style={{
                      marginTop: '8px',
                      padding: '6px 12px',
                      background: '#667eea',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.85rem'
                    }}
                  >
                    Try Again
                  </button>
                </div>
              </div>
            )}

            <div className="diagram-container" style={{
              position: 'relative',
              overflow: 'hidden',
              border: '1px solid #ddd',
              borderRadius: '8px',
              background: '#fff',
              minHeight: '250px'
            }}>
              {isGeneratingDiagram ? (
                <div style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '250px',
                  flexDirection: 'column',
                  gap: '16px'
                }}>
                  <RefreshCw size={32} className="spinning" />
                  <p>{i18n.t('doc.processing.diagram')}</p>
                </div>
              ) : isEditingDiagram ? (
                <div style={{ height: '250px' }}>
                  <textarea
                    value={editedDiagram}
                    onChange={(e) => setEditedDiagram(e.target.value)}
                    style={{
                      width: '100%',
                      height: '100%',
                      border: 'none',
                      outline: 'none',
                      padding: '16px',
                      fontFamily: 'monospace',
                      fontSize: '14px',
                      resize: 'none'
                    }}
                    placeholder="Enter your Mermaid diagram code here..."
                  />
                </div>
              ) : (
                <div
                  ref={diagramRef}
                  style={{
                    transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
                    transformOrigin: 'top left',
                    transition: 'transform 0.1s ease-out',
                    minHeight: '250px',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    padding: '10px'
                  }}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onWheel={(e) => handleWheel(e as unknown as WheelEvent)}
                />
              )}
            </div>

            {/* Zoom Controls */}
            {!isEditingDiagram && (
              <div className="zoom-controls" style={{
                position: 'absolute',
                bottom: '16px',
                right: '16px',
                display: 'flex',
                gap: '8px',
                background: 'white',
                padding: '8px',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}>
                <button onClick={handleZoomOut} className="btn-zoom">
                  <ZoomOut size={16} />
                </button>
                <button onClick={handleResetView} className="btn-zoom">
                  <Maximize2 size={16} />
                </button>
                <button onClick={handleZoomIn} className="btn-zoom">
                  <ZoomIn size={16} />
                </button>
              </div>
            )}
          </div>

          {/* Code Explanation Section */}
          {(codeExplanation || explanationError) && (
            <div className="content-section explanation-section">
              <div className="section-header">
                <div className="section-title-wrapper">
                  <h2 className="section-title">
                    <div className="title-icon">
                      <BookOpen size={22} />
                    </div>
                    <span className="title-text">{i18n.t('doc.code.explanation')}</span>
                    <div className="status-badge level-badge">
                      <span className="badge-dot"></span>
                      {explanationLevel === 'high' ? (i18n.t('doc.high.level') || 'High Level') : (i18n.t('doc.low.level') || 'Low Level')}
                    </div>
                  </h2>
                  <p className="section-description">
                    {i18n.t('doc.explanation.description') || `Detailed code analysis and explanation at ${explanationLevel} level`}
                  </p>
                </div>
              </div>
              {explanationError ? (
                <div style={{
                  background: '#fff5f5',
                  border: '1px solid #fc8181',
                  borderRadius: '8px',
                  padding: '16px',
                  margin: '20px 28px',
                  color: '#c53030'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <AlertTriangle size={20} />
                    <strong>Error generating explanation:</strong>
                  </div>
                  <p style={{ margin: '0 0 12px 0' }}>{explanationError}</p>
                  <button
                    onClick={() => {
                      setExplanationError(null);
                      generateCodeExplanation();
                    }}
                    style={{
                      padding: '8px 16px',
                      background: '#667eea',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.9rem'
                    }}
                  >
                    Try Again
                  </button>
                </div>
              ) : (
                <div className="explanation-content">
                  <div>
                    <pre style={{
                      whiteSpace: 'pre-wrap',
                      background: '#f8f9fa',
                      padding: '24px',
                      borderRadius: '12px',
                      overflow: 'auto',
                      maxHeight: '500px',
                      margin: '0',
                      border: '1px solid #e2e8f0',
                      lineHeight: '1.7',
                      fontSize: '0.95rem',
                      fontFamily: 'system-ui, -apple-system, sans-serif'
                    }}>
                      {codeExplanation}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Generated Document Section */}
          {generatedDocument && (
            <div className="content-section document-section">
              <div className="section-header">
                <div className="section-title-wrapper">
                  <h2 className="section-title">
                    <div className="title-icon">
                      <FileText size={22} />
                    </div>
                    <span className="title-text">{i18n.t('doc.generated.document')}</span>
                    <div className="status-badges">
                      <div className="status-badge format-badge">
                        <span className="badge-dot"></span>
                        {documentFormat.toUpperCase()}
                      </div>
                      <div className="status-badge level-badge">
                        <span className="badge-dot"></span>
                        {explanationLevel === 'high' ? (i18n.t('doc.high.level') || 'High Level') : (i18n.t('doc.low.level') || 'Low Level')}
                      </div>
                    </div>
                  </h2>
                  <p className="section-description">
                    {i18n.t('doc.document.description') || `Generated ${documentFormat} document with comprehensive code documentation`}
                  </p>
                </div>
              </div>
              <div className="document-content">
                <pre style={{
                  whiteSpace: 'pre-wrap',
                  background: '#f8f9fa',
                  padding: '24px',
                  borderRadius: '12px',
                  overflow: 'auto',
                  maxHeight: '600px',
                  margin: '0',
                  border: '1px solid #e2e8f0',
                  lineHeight: '1.7',
                  fontSize: '0.95rem',
                  fontFamily: 'system-ui, -apple-system, sans-serif'
                }}>
                  {generatedDocument}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </DiagramErrorBoundary>
  );
};

export default DocumentGenerationPage;