import React, { useState, useEffect } from 'react';
import {
  Code, FileText, Download, Eye, Star,
  TrendingUp, Activity, Clock, Zap, BookOpen, Send
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import extendedApiService from '../services/extendedApi.service.ts';
import type {
  AIExplanationRequest,
  ExplanationEvaluationRequest,
  HumanReviewRequest
} from '../services/extendedApi.service.ts';
import './DeveloperDashboard.css';

interface Analysis {
  id: string;
  projectName: string;
  analysisType: string;
  status: 'completed' | 'in-progress' | 'pending';
  createdAt: string;
  exportAvailable: boolean;
}

interface Explanation {
  id: string;
  codeSnippet: string;
  question: string;
  language: string;
  explanation: string;
  confidence: number;
  timestamp: string;
  evaluations: ExplanationEvaluation[];
}

interface ExplanationEvaluation {
  id: string;
  explanationId: string;
  rating: number;
  feedback: string;
  evaluatorId: string;
  createdAt: string;
}

const DeveloperDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [explanations, setExplanations] = useState<Explanation[]>([]);
  const [selectedExplanation, setSelectedExplanation] = useState<Explanation | null>(null);
  const [evaluationHistory, setEvaluationHistory] = useState<ExplanationEvaluation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'analyses' | 'explanations' | 'evaluations'>('analyses');

  // Form states
  const [newExplanationRequest, setNewExplanationRequest] = useState<AIExplanationRequest>({
    code_snippet: '',
    question: '',
    language: 'python'
  });
  const [evaluationForm, setEvaluationForm] = useState<ExplanationEvaluationRequest>({
    explanation_id: '',
    rating: 5,
    feedback: ''
  });
  const [humanReviewForm, setHumanReviewForm] = useState<HumanReviewRequest>({
    analysis_id: '',
    review_data: {
      approved: false,
      comments: '',
      suggestions: []
    }
  });

  useEffect(() => {
    loadDeveloperData();
  }, []);

  const loadDeveloperData = async () => {
    try {
      setIsLoading(true);

      // Load analyses (mock data for now - would come from existing API)
      const mockAnalyses: Analysis[] = [
        {
          id: '1',
          projectName: 'E-commerce Backend',
          analysisType: 'Class Diagram',
          status: 'completed',
          createdAt: '2024-01-15T10:30:00Z',
          exportAvailable: true
        },
        {
          id: '2',
          projectName: 'User Authentication',
          analysisType: 'Logic Explanation',
          status: 'in-progress',
          createdAt: '2024-01-16T14:20:00Z',
          exportAvailable: false
        }
      ];
      setAnalyses(mockAnalyses);

      // Load AI explanations
      const explanationsData = await extendedApiService.getAIExplanations();
      setExplanations(explanationsData.map((exp: any) => ({
        id: exp.id || Math.random().toString(),
        codeSnippet: exp.code_snippet || '',
        question: exp.question || '',
        language: exp.language || 'python',
        explanation: exp.explanation || '',
        confidence: exp.confidence || 0,
        timestamp: exp.timestamp || new Date().toISOString(),
        evaluations: []
      })));

    } catch (error) {
      console.error('Failed to load developer data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportAnalysis = async (analysisId: string, format: 'pdf' | 'markdown') => {
    try {
      const blob = await extendedApiService.exportAnalysis(analysisId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analysis-${analysisId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to export analysis:', error);
    }
  };

  const handleRequestExplanation = async () => {
    try {
      const response = await extendedApiService.requestAIExplanation(newExplanationRequest);
      setExplanations([{
        id: Math.random().toString(),
        codeSnippet: newExplanationRequest.code_snippet,
        question: newExplanationRequest.question || '',
        language: newExplanationRequest.language || 'python',
        explanation: response.explanation,
        confidence: response.confidence,
        timestamp: response.timestamp,
        evaluations: []
      }, ...explanations]);

      // Reset form
      setNewExplanationRequest({
        code_snippet: '',
        question: '',
        language: 'python'
      });
    } catch (error) {
      console.error('Failed to request AI explanation:', error);
    }
  };

  const handleEvaluateExplanation = async (explanationId: string) => {
    try {
      const evaluationRequest = {
        explanation_id: explanationId,
        rating: evaluationForm.rating,
        feedback: evaluationForm.feedback
      };

      const response = await extendedApiService.evaluateExplanation(explanationId, evaluationRequest);

      // Update local state
      setExplanations(explanations.map(exp =>
        exp.id === explanationId
          ? {
            ...exp, evaluations: [...exp.evaluations, {
              id: response.id,
              explanationId: response.explanation_id,
              rating: response.rating,
              feedback: response.feedback,
              evaluatorId: response.evaluator_id,
              createdAt: response.created_at
            }]
          }
          : exp
      ));

      // Reset form
      setEvaluationForm({
        explanation_id: '',
        rating: 5,
        feedback: ''
      });
    } catch (error) {
      console.error('Failed to evaluate explanation:', error);
    }
  };

  const handleViewEvaluationHistory = async (explanationId: string) => {
    try {
      const history = await extendedApiService.getEvaluationHistory(explanationId);
      setEvaluationHistory(history.map((item: any) => ({
        id: item.id,
        explanationId: item.explanation_id,
        rating: item.rating,
        feedback: item.feedback,
        evaluatorId: item.evaluator_id,
        createdAt: item.created_at
      })));
      setSelectedExplanation(explanations.find(exp => exp.id === explanationId) || null);
    } catch (error) {
      console.error('Failed to load evaluation history:', error);
    }
  };

  const handleSubmitHumanReview = async () => {
    try {
      await extendedApiService.submitHumanReview(
        humanReviewForm.analysis_id,
        humanReviewForm
      );

      // Update analysis status
      setAnalyses(analyses.map(analysis =>
        analysis.id === humanReviewForm.analysis_id
          ? { ...analysis, status: 'completed' as const }
          : analysis
      ));

      // Reset form
      setHumanReviewForm({
        analysis_id: '',
        review_data: {
          approved: false,
          comments: '',
          suggestions: []
        }
      });
    } catch (error) {
      console.error('Failed to submit human review:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'in-progress': return '#f59e0b';
      case 'pending': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981';
    if (confidence >= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  if (isLoading) {
    return (
      <div className="developer-dashboard">
        <div className="loading-container">
          <Activity className="loading-icon" />
          <p>Loading developer dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="developer-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <Code className="header-icon" />
            <h1>Developer Dashboard</h1>
          </div>
          <div className="header-right">
            <span className="user-info">Welcome, {user?.username}</span>
            <button onClick={logout} className="logout-btn">
              LogOut
            </button>
          </div>
        </div>
      </header>

      <div className="dashboard-tabs">
        <button
          className={`tab-btn ${activeTab === 'analyses' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyses')}
        >
          <FileText />
          Analyses
        </button>
        <button
          className={`tab-btn ${activeTab === 'explanations' ? 'active' : ''}`}
          onClick={() => setActiveTab('explanations')}
        >
          <BookOpen />
          AI Explanations
        </button>
        <button
          className={`tab-btn ${activeTab === 'evaluations' ? 'active' : ''}`}
          onClick={() => setActiveTab('evaluations')}
        >
          <Star />
          Evaluations
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === 'analyses' && (
          <div className="analyses-section">
            <div className="section-header">
              <h2>Analysis Results</h2>
              <div className="section-stats">
                <div className="stat-item">
                  <TrendingUp />
                  <span>{analyses.filter(a => a.status === 'completed').length} Completed</span>
                </div>
                <div className="stat-item">
                  <Clock />
                  <span>{analyses.filter(a => a.status === 'in-progress').length} In Progress</span>
                </div>
              </div>
            </div>

            <div className="analyses-grid">
              {analyses.map(analysis => (
                <div key={analysis.id} className="analysis-card">
                  <div className="card-header">
                    <h3>{analysis.projectName}</h3>
                    <span
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(analysis.status) }}
                    >
                      {analysis.status}
                    </span>
                  </div>
                  <div className="card-content">
                    <p><strong>Type:</strong> {analysis.analysisType}</p>
                    <p><strong>Created:</strong> {new Date(analysis.createdAt).toLocaleDateString()}</p>
                    {analysis.exportAvailable && (
                      <div className="export-actions">
                        <button
                          onClick={() => handleExportAnalysis(analysis.id, 'pdf')}
                          className="export-btn"
                        >
                          <Download />
                          PDF
                        </button>
                        <button
                          onClick={() => handleExportAnalysis(analysis.id, 'markdown')}
                          className="export-btn"
                        >
                          <FileText />
                          Markdown
                        </button>
                      </div>
                    )}
                    {analysis.status === 'completed' && (
                      <div className="human-review-section">
                        <h4>Submit Human Review</h4>
                        <textarea
                          placeholder="Comments about the analysis..."
                          value={humanReviewForm.review_data.comments}
                          onChange={(e) => setHumanReviewForm({
                            ...humanReviewForm,
                            analysis_id: analysis.id,
                            review_data: {
                              ...humanReviewForm.review_data,
                              comments: e.target.value
                            }
                          } as HumanReviewRequest)}
                        />
                        <div className="review-actions">
                          <label>
                            <input
                              type="checkbox"
                              checked={humanReviewForm.review_data.approved}
                              onChange={(e) => setHumanReviewForm({
                                ...humanReviewForm,
                                analysis_id: analysis.id,
                                review_data: {
                                  ...humanReviewForm.review_data,
                                  approved: e.target.checked
                                }
                              } as HumanReviewRequest)}
                            />
                            Approve Analysis
                          </label>
                          <button
                            onClick={handleSubmitHumanReview}
                            className="submit-review-btn"
                          >
                            <Send />
                            Submit Review
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'explanations' && (
          <div className="explanations-section">
            <div className="section-header">
              <h2>AI Explanations</h2>
              <button className="new-explanation-btn" onClick={() => setActiveTab('explanations')}>
                <Zap />
                Request New Explanation
              </button>
            </div>

            <div className="new-explanation-form">
              <h3>Request AI Explanation</h3>
              <div className="form-group">
                <label>Code Snippet:</label>
                <textarea
                  placeholder="Paste your code here..."
                  value={newExplanationRequest.code_snippet}
                  onChange={(e) => setNewExplanationRequest({
                    ...newExplanationRequest,
                    code_snippet: e.target.value
                  } as AIExplanationRequest)}
                />
              </div>
              <div className="form-group">
                <label>Question:</label>
                <input
                  type="text"
                  placeholder="What would you like to know about this code?"
                  value={newExplanationRequest.question}
                  onChange={(e) => setNewExplanationRequest({
                    ...newExplanationRequest,
                    question: e.target.value
                  } as AIExplanationRequest)}
                />
              </div>
              <div className="form-group">
                <label>Language:</label>
                <select
                  value={newExplanationRequest.language}
                  onChange={(e) => setNewExplanationRequest({
                    ...newExplanationRequest,
                    language: e.target.value
                  } as AIExplanationRequest)}
                >
                  <option value="python">Python</option>
                  <option value="java">Java</option>
                  <option value="javascript">JavaScript</option>
                  <option value="typescript">TypeScript</option>
                </select>
              </div>
              <button onClick={handleRequestExplanation} className="request-btn">
                <Send />
                Request Explanation
              </button>
            </div>

            <div className="explanations-list">
              {explanations.map(explanation => (
                <div key={explanation.id} className="explanation-card">
                  <div className="card-header">
                    <h3>Explanation</h3>
                    <span
                      className="confidence-badge"
                      style={{ backgroundColor: getConfidenceColor(explanation.confidence) }}
                    >
                      {Math.round(explanation.confidence * 100)}% Confidence
                    </span>
                  </div>
                  <div className="card-content">
                    <div className="code-snippet">
                      <pre><code>{explanation.codeSnippet}</code></pre>
                    </div>
                    <div className="question">
                      <strong>Question:</strong> {explanation.question}
                    </div>
                    <div className="explanation">
                      <strong>AI Explanation:</strong> {explanation.explanation}
                    </div>
                    <div className="explanation-actions">
                      <button
                        onClick={() => handleViewEvaluationHistory(explanation.id)}
                        className="view-history-btn"
                      >
                        <Eye />
                        View Evaluation History
                      </button>
                      <button
                        onClick={() => {
                          setEvaluationForm({ ...evaluationForm, explanation_id: explanation.id } as ExplanationEvaluationRequest);
                          setActiveTab('evaluations');
                        }}
                        className="evaluate-btn"
                      >
                        <Star />
                        Evaluate
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'evaluations' && (
          <div className="evaluations-section">
            <div className="section-header">
              <h2>Evaluations</h2>
            </div>

            {selectedExplanation && (
              <div className="evaluation-history">
                <h3>Evaluation History for Explanation</h3>
                <div className="selected-explanation">
                  <p><strong>Question:</strong> {selectedExplanation.question}</p>
                  <p><strong>Explanation:</strong> {selectedExplanation.explanation}</p>
                </div>
                <div className="history-list">
                  {evaluationHistory.map(evaluation => (
                    <div key={evaluation.id} className="evaluation-item">
                      <div className="evaluation-header">
                        <span className="rating">Rating: {evaluation.rating}/5</span>
                        <span className="date">{new Date(evaluation.createdAt).toLocaleDateString()}</span>
                      </div>
                      <p className="feedback">{evaluation.feedback}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="new-evaluation-form">
              <h3>Submit New Evaluation</h3>
              <div className="form-group">
                <label>Explanation ID:</label>
                <input
                  type="text"
                  value={evaluationForm.explanation_id}
                  onChange={(e) => setEvaluationForm({
                    ...evaluationForm,
                    explanation_id: e.target.value
                  } as ExplanationEvaluationRequest)}
                  placeholder="Enter explanation ID"
                />
              </div>
              <div className="form-group">
                <label>Rating (1-5):</label>
                <select
                  value={evaluationForm.rating}
                  onChange={(e) => setEvaluationForm({
                    ...evaluationForm,
                    rating: parseInt(e.target.value)
                  } as ExplanationEvaluationRequest)}
                >
                  {[1, 2, 3, 4, 5].map(rating => (
                    <option key={rating} value={rating}>{rating}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Feedback:</label>
                <textarea
                  placeholder="Provide your feedback..."
                  value={evaluationForm.feedback}
                  onChange={(e) => setEvaluationForm({
                    ...evaluationForm,
                    feedback: e.target.value
                  } as ExplanationEvaluationRequest)}
                />
              </div>
              <button
                onClick={() => evaluationForm.explanation_id && handleEvaluateExplanation(evaluationForm.explanation_id)}
                className="submit-evaluation-btn"
              >
                <Send />
                Submit Evaluation
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DeveloperDashboard;
