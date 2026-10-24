import React, { useState, useEffect } from 'react';
import {
  FileText, Eye, BarChart3, TrendingUp,
  LogOut, CheckCircle, Clock, AlertCircle,
  Activity, Send, Star, MessageSquare, Sun, Moon,
  Menu, X, Shield, Lock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import extendedApiService, {
  type ExplanationEvaluationRequest
} from '../services/extendedApi.service';
import apiClient from '../services/apiClient';
import { type StatsData, type EvalStatsData } from './ReviewerDashboard/types';
import './ReviewerDashboard.css';
import '../Dashboard-Modern.css';

// ─── Interfaces ──────────────────────────────────────────────────────────────
interface ExplanationEvaluation {
  explanation_id: string; content: string; exp_type: string;
  created_at: string; evaluation?: {
    final_score: number; final_percentage: number; verdict: string;
    evaluated_at: string; layer_scores: {
      ast_cross_check: number; completeness: number; llm_judge: number; human_review: number | null;
    };
  };
}
// New evaluation history API shape
interface EvalLayerScores {
  ast_cross_check?: number; completeness?: number;
  llm_judge?: number; human_review?: number;
}
interface EvalDetail {
  final_score: number; final_percentage: number; verdict: string;
  evaluated_at: string; layer_scores: EvalLayerScores;
}
interface NotifyAdminForm { title: string; message: string; related_id: string; related_type: string; }
interface EvaluationForm { explanation_id: string; rating: number; feedback: string; }

// ─── New interfaces for real API tabs ────────────────────────────────────────
interface RawAnalysisResult {
  id: string; _id?: string; code_file_id: string; analysis_type?: string;
  status: string; created_at: string; started_at?: string;
  completed_at?: string; error_message?: string | null; score?: number;
}
interface RawJob {
  id: string; _id?: string; code_file_id: string; status: string;
  created_at: string; started_at?: string; completed_at?: string | null;
  error_message?: string | null;
}
interface ExplanationDetail {
  id: string; explanation_id: string; content: string; exp_type: string;
  created_at: string; evaluation?: any;
}
interface RawExplanation {
  _id: string; analysis_id: string; explanation_type: string; created_at: string;
}
interface RawAiTask {
  _id?: string; id?: string;
  task_id?: string;
  analysis_id?: string;
  exp_type?: string;
  status?: string;
  completed_at?: string;
  result?: {
    status?: string;
    explanation_id?: string;
    type?: string;
    content?: string;
  };
}
interface RawGeneratedFile {
  _id: string; explanation_id: string; analysis_id: string; project_id: string | null;
  filename: string; file_type: string; file_size: number;
  created_at: string; downloaded_count: number;
}

// ─── ThroughputChart ─────────────────────────────────────────────────────────
import ThroughputChart from './ReviewerDashboard/ThroughputChart';
import QueueGauge from './ReviewerDashboard/QueueGauge';
import DurationByLanguageCard from './ReviewerDashboard/DurationByLanguageCard';
import ErrorClassificationCard from './ReviewerDashboard/ErrorClassificationCard';
import GeneratedFilesCard from './ReviewerDashboard/GeneratedFilesCard';
import SizeDistributionCard from './ReviewerDashboard/SizeDistributionCard';
import CeleryHealthCard from './ReviewerDashboard/CeleryHealthCard';
import VerifierStatsCard from './ReviewerDashboard/VerifierStatsCard';
import EvalStatsCard from './ReviewerDashboard/EvalStatsCard';

const ReviewerDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [analysisResults, setAnalysisResults] = useState<RawAnalysisResult[]>([]);
  const [jobsStatus, setJobsStatus] = useState<RawJob[]>([]);
  const [explanations, setExplanations] = useState<RawExplanation[]>([]);
  const [aiTasks, setAiTasks] = useState<RawAiTask[]>([]);
  const [generatedFiles, setGeneratedFiles] = useState<RawGeneratedFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [tabLoading, setTabLoading] = useState(false);
  const [detailModal, setDetailModal] = useState<{ type: string; data: any } | null>(null);
  const [activeTab, setActiveTab] = useState<'results' | 'jobs' | 'explanations' | 'files' | 'stats' | 'evaluations'>('results');
  const [showNotifyAdmin, setShowNotifyAdmin] = useState(false);
  const [notifyForm, setNotifyForm] = useState<NotifyAdminForm>({ title: '', message: '', related_id: '', related_type: '' });
  const [statsData, setStatsData] = useState<StatsData | null>(null);
  const [evalStats, setEvalStats] = useState<EvalStatsData | null>(null);
  const [evaluationHistory, setEvaluationHistory] = useState<ExplanationEvaluation[]>([]);
    const [useMockData, setUseMockData] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  // Evaluation modal (per-explanation)
  const [evalModal, setEvalModal] = useState<any>(null);
  const [evalScore, setEvalScore] = useState('90');
  const [evalComment, setEvalComment] = useState('');
  const [evalSuccess, setEvalSuccess] = useState(false);
  const [evalSubmitting, setEvalSubmitting] = useState(false);
  // Change password modal
  const [showChangePwd, setShowChangePwd] = useState(false);
  const [pwdForm, setPwdForm] = useState({ old_password: '', new_password: '', confirm_new_password: '' });
  const [pwdError, setPwdError] = useState('');
  const [pwdSuccess, setPwdSuccess] = useState(false);
  const [pwdSubmitting, setPwdSubmitting] = useState(false);

  const MOCK: StatsData = {
    throughput_24h: 42, avg_processing_time_ms: 350, avg_queue_time_ms: 120,
    active_tasks: 3, total_explanations: 15, reserved_tasks: 2, retried_tasks: 0, celery_status: 'healthy',
    duration_by_language: { python: { avg_duration_ms: 320, count: 8 }, java: { avg_duration_ms: 580, count: 4 }, javascript: { avg_duration_ms: 210, count: 6 }, csharp: { avg_duration_ms: 440, count: 2 } },
    error_classification: { Security: 3, Logic: 7, Style: 12, Performance: 5 }, total_failed: 27,
    size_distribution: { under_50KB: 8, '50_to_200KB': 5, over_200KB: 2 },
    generated_files: { markdown: { count: 6, avg_size_bytes: 3800, max_size_bytes: 5200, total_downloads: 9 }, pdf: { count: 9, avg_size_bytes: 58000, max_size_bytes: 72000, total_downloads: 14 } },
    verifier_by_type: { high_level: { total: 8, verifier_success: 6, verifier_fallbacks: 2, fallback_rate_percent: 25 }, low_level: { total: 5, verifier_success: 4, verifier_fallbacks: 1, fallback_rate_percent: 20 } },
    verifier_overall: { total_explanations: 13, verifier_fallbacks: 3, fallback_rate_percent: 23 },
  };
  const MOCK_EVAL: EvalStatsData = {
    total_evaluations: 13, average_score: .74,
    verdict_distribution: [{ _id: 'EXCELLENT', count: 3 }, { _id: 'GOOD', count: 5 }, { _id: 'ACCEPTABLE', count: 4 }, { _id: 'POOR', count: 1 }],
  };

  // ── Core fetch: always show all cards — use real data, fallback values ensure cards render ──
  const fetchStats = async (mock: boolean) => {
    if (mock) { setStatsData({ ...MOCK }); setEvalStats({ ...MOCK_EVAL }); return; }
    try {
      const res = await apiClient.get('/api/analysis/reviewer/stats/');
      const s = res.data, perf = s.performance || {}, celery = s.celery || {}, quality = s.quality || {};
      const overall = quality.verifier_stats?.overall || {}, byType = quality.verifier_stats?.by_type || {};
      const errorCls = quality.error_classification || {}, files = s.files || {};
      // Map real data — all fields have fallbacks so cards always render
      setStatsData({
        throughput_24h: perf.throughput_24h ?? 0,
        avg_processing_time_ms: perf.avg_processing_time_ms ?? 0,
        avg_queue_time_ms: perf.avg_queue_time_ms ?? 0,
        active_tasks: celery.active_tasks ?? 0,
        reserved_tasks: celery.reserved_tasks ?? 0,
        retried_tasks: celery.retried_tasks ?? 0,
        celery_status: celery.status ?? 'unknown',
        total_explanations: overall.total_explanations ?? 0,
        duration_by_language: perf.duration_by_language ?? {},
        error_classification: errorCls ?? {},
        total_failed: (errorCls as any)?.total_failed ?? 0,
        size_distribution: files.size_distribution ?? { under_50KB: 0, '50_to_200KB': 0, over_200KB: 0 },
        generated_files: files.generated_files ?? {},
        verifier_by_type: byType,
        verifier_overall: {
          total_explanations: overall.total_explanations ?? 0,
          verifier_fallbacks: overall.verifier_fallbacks ?? 0,
          fallback_rate_percent: overall.fallback_rate_percent ?? 0,
        },
      });
    } catch (e) { console.error('Stats fetch failed:', e); }
    try {
      const er = await apiClient.get('/api/analysis/evaluation-stats/');
      setEvalStats(er.data);
    } catch (e) { console.error('EvalStats fetch failed:', e); }
    try {
      const eh = await apiClient.get('/api/analysis/evaluation-history/');
      setEvaluationHistory(eh.data.explanations || []);
    } catch (e) { console.error('Evaluation history fetch failed:', e); }
  };

  // Fetch tab data on demand — each tab calls its own endpoint
  const fetchTabData = async (tab: string) => {
    setTabLoading(true);
    try {
      if (tab === 'results') {
        const r = await apiClient.get('/api/analysis/analysis-results/');
        const rd = r.data;
        setAnalysisResults(Array.isArray(rd) ? rd : rd?.results || rd?.data || []);
      } else if (tab === 'jobs') {
        const j = await apiClient.get('/api/analysis/analysis-jobs/');
        const jd = j.data;
        setJobsStatus(Array.isArray(jd) ? jd : jd?.results || jd?.data || []);
      } else if (tab === 'explanations') {
        const [exp, tasks] = await Promise.all([
          apiClient.get('/api/analysis/ai-explanations/'),
          apiClient.get('/api/analysis/reviewer/ai-tasks/').catch(() => ({ data: [] })),
        ]);
        const ed = exp.data;
        setExplanations(Array.isArray(ed) ? ed : ed?.results || ed?.data || []);
        const td = tasks.data;
        setAiTasks(Array.isArray(td) ? td : td?.tasks || td?.results || td?.data || []);
        // Fetch evalHistory separately so its failure doesn't affect other data
        try {
          const evalHist = await apiClient.get('/api/analysis/evaluation-history/');
          const ehd = evalHist.data;
          const items: ExplanationEvaluation[] = Array.isArray(ehd) ? ehd : ehd?.explanations || [];
          setEvaluationHistory(items);
        } catch (e) {
          console.error('evalHistory fetch failed:', e);
          setEvaluationHistory([]);
        }
      } else if (tab === 'files') {
        const f = await apiClient.get('/api/analysis/generated-files/');
        const fd = f.data;
        setGeneratedFiles(Array.isArray(fd) ? fd : fd?.files || fd?.results || fd?.data || []);
      }
    } catch (e) { console.error(`Tab ${tab} fetch failed:`, e); }
    setTabLoading(false);
  };

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      await Promise.all([fetchTabData('results'), fetchStats(false)]);
      setIsLoading(false);
    };
    load();
  }, []);

  // Reload tab data when switching tabs
  useEffect(() => { fetchTabData(activeTab); }, [activeTab]);

  useEffect(() => { fetchStats(useMockData); }, [useMockData]);

  const handleLogout = () => logout();

  // Cycle tab label during loading
  const [rdLoadingLabel, setRdLoadingLabel] = React.useState('Analysis Results');
  useEffect(() => {
    if (!isLoading) return;
    const labels = ['Analysis Results', 'Job Status', 'Explanations', 'Generated Files', 'Statistics', 'Evaluations'];
    let idx = 1;
    const interval = setInterval(() => {
      setRdLoadingLabel(labels[idx % 6]);
      idx++;
    }, 1000);
    return () => clearInterval(interval);
  }, [isLoading]);

  if (isLoading) {
    const rdTabData = [
      { icon: <FileText />, label: 'Analysis Results' },
      { icon: <Activity />, label: 'Job Status' },
      { icon: <MessageSquare />, label: 'Explanations' },
      { icon: <Eye />, label: 'Generated Files' },
      { icon: <BarChart3 />, label: 'Statistics' },
      { icon: <Star />, label: 'Evaluations' },
    ];
    return (
      <div className={`rd-loading-screen ${isDark ? 'rd-dark' : 'rd-light'}`}>
        <div className="rd-orbit-container">
          <div className="rd-center-glow" />
          {rdTabData.map((tab, i) => (
            <div key={i} className="rd-orbit-icon">{tab.icon}</div>
          ))}
        </div>
        <div className="rd-tab-label"><span key={rdLoadingLabel}>{rdLoadingLabel}</span></div>
        <div className="rd-loading-text">
          <p className="rd-loading-title">Reviewer Dashboard</p>
          <p className="rd-loading-subtitle">
            Loading
            <span className="rd-loading-dot" />
            <span className="rd-loading-dot" />
            <span className="rd-loading-dot" />
          </p>
        </div>
        <div className="rd-loading-line" />
      </div>
    );
  }

  return (
    <div className={`rd-layout ${isDark ? 'rd-dark' : 'rd-light'}${isSidebarOpen ? ' sidebar-open' : ''}`}>

      {/* ── Header ──────────────────────────────────────────────────── */}
      <header className="rd-topbar">
        <div className="rd-topbar-left">
          <button className="rd-sidebar-toggle" onClick={() => setIsSidebarOpen(o => !o)}>
            {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="rd-logo">
            <div className="rd-logo-icon"><FileText size={18} /></div>
            <span className="rd-logo-text">AutoTestDocGen</span>
          </div>
        </div>
        <div className="rd-topbar-right">
          <button onClick={() => setIsDark(d => !d)} className="unified-theme-toggle" title="Toggle theme">
            {isDark ? <Sun width={16} height={16} style={{ color: '#f59e0b' }} /> : <Moon width={16} height={16} style={{ color: '#764ba2' }} />}
          </button>
        </div>
      </header>

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className={`rd-sidebar${isSidebarOpen ? ' open' : ' closed'}`}>
        <nav className="rd-sidebar-nav">
          {([
            { id: 'results',      label: 'Analysis Results', icon: <FileText size={18} /> },
            { id: 'jobs',         label: 'Job Status',       icon: <Activity size={18} /> },
            { id: 'explanations', label: 'Explanations',     icon: <MessageSquare size={18} /> },
            { id: 'files',        label: 'Generated Files',  icon: <Eye size={18} /> },
            { id: 'stats',        label: 'Statistics',       icon: <BarChart3 size={18} /> },
            { id: 'evaluations',  label: 'Evaluation History', icon: <Star size={18} /> },
          ] as const).map(({ id, label, icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`rd-nav-item${activeTab === id ? ' active' : ''}`}
            >
              {icon}
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="rd-sidebar-footer">
          <div className="rd-user-profile">
            <div className="rd-user-avatar">{user?.username?.charAt(0).toUpperCase() || 'R'}</div>
            <div className="rd-user-details">
              <div className="rd-user-name">{user?.username || 'Reviewer'}</div>
              <div className="rd-user-role">Reviewer</div>
            </div>
          </div>
          <div className="rd-sidebar-actions">
            <button
              onClick={() => { setShowChangePwd(true); setPwdForm({ old_password: '', new_password: '', confirm_new_password: '' }); setPwdError(''); setPwdSuccess(false); }}
              className="rd-action-btn"
            >
              <Lock size={15} />
              <span>Change Password</span>
            </button>
            <button onClick={handleLogout} className="rd-action-btn rd-logout-btn">
              <LogOut size={15} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────── */}
      <main className={`rd-main${isSidebarOpen ? '' : ' sidebar-closed'}`}>

        {/* KPI cards */}
        <div className="rd-kpi-grid">
          {[
            { icon: <CheckCircle className="w-8 h-8 text-green-600" />, label: 'Total Jobs',        value: statsData?.total_explanations ?? 0 },
            { icon: <Activity    className="w-8 h-8 text-yellow-600" />, label: 'Active Tasks',      value: statsData?.active_tasks ?? 0 },
            { icon: <TrendingUp  className="w-8 h-8 text-purple-600" />, label: 'Throughput (24h)', value: statsData?.throughput_24h ?? 0 },
            { icon: <Clock       className="w-8 h-8 text-blue-600"   />, label: 'Avg Processing',   value: `${statsData?.avg_processing_time_ms ?? 0}ms` },
          ].map(({ icon, label, value }) => (
            <div key={label} className="rd-kpi">
              <div className="flex items-center">{icon}<div className="ml-3"><p className={`text-sm font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{label}</p><p className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{value}</p></div></div>
            </div>
          ))}
        </div>

        {tabLoading && <div className={`flex items-center justify-center gap-2 py-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-400'}`}><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500" />Loading...</div>}

        {/* ── Analysis Results Tab ── */}
        {activeTab === 'results' && (
          <div className="rd-card">
            <div className="px-6 py-4 border-b flex justify-between items-center rd-card-header">
              <h2 className={`text-lg font-semibold flex items-center gap-2 ${isDark ? 'text-gray-100' : 'text-gray-900'}`}><FileText className="w-5 h-5 text-blue-500" />Analysis Results<span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{analysisResults.length}</span></h2>
            </div>
            <div className="overflow-x-auto">
              {analysisResults.length === 0
                ? <p className="text-center text-gray-400 py-14 text-sm">No analysis results yet.</p>
                : <table className="rd-table">
                  <thead><tr>
                    {['ID', 'Code File', 'Status', 'Created', 'Started', 'Completed', 'Error', 'Actions'].map(h =>
                      <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${isDark ? 'text-gray-300' : 'text-gray-500'}`}>{h}</th>
                    )}
                  </tr></thead>
                  <tbody className="divide-y divide-gray-50">
                    {analysisResults.map((r, i) => {
                      const id = r.id || r._id || '';
                      const st = (r.status || '').toUpperCase();
                      const sc = st === 'COMPLETED' ? 'bg-green-100 text-green-700' : st === 'STARTED' || st === 'RUNNING' ? 'bg-yellow-100 text-yellow-700' : st === 'FAILED' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500';
                      return <tr key={id || i} className={isDark ? 'hover:bg-gray-700 transition-colors' : 'hover:bg-blue-50/50 transition-colors'}>
                        <td className="px-4 py-3"><code className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded" title={id}>{id.slice(-10)}</code></td>
                        <td className="px-4 py-3"><code className="text-xs text-gray-500" title={r.code_file_id}>{(r.code_file_id || '').slice(-10)}</code></td>
                        <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-semibold ${sc}`}>{r.status}</span></td>
                        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{r.created_at ? new Date(r.created_at).toLocaleString() : '-'}</td>
                        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{r.started_at ? new Date(r.started_at).toLocaleString() : '-'}</td>
                        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{r.completed_at ? new Date(r.completed_at).toLocaleString() : '-'}</td>
                        <td className="px-4 py-3">{r.error_message ? <span className="text-xs text-red-500 bg-red-50 px-2 py-1 rounded">{r.error_message}</span> : <span className="text-xs text-green-400">—</span>}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            <button onClick={() => setDetailModal({ type: 'result', data: r })} className="rd-btn rd-btn-secondary"><Eye className="w-3 h-3" />View</button>
                            <button onClick={() => { setNotifyForm({ title: '', message: '', related_id: id, related_type: 'analysis_result' }); setShowNotifyAdmin(true); }} className="flex items-center gap-1 px-2.5 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-xs font-medium transition"><MessageSquare className="w-3 h-3" />Notify</button>
                          </div>
                        </td>
                      </tr>;
                    })}
                  </tbody>
                </table>
              }
            </div>
          </div>
        )}

        {/* ── Job Status Tab ── */}
        {activeTab === 'jobs' && (
          <div className="rd-card">
            <div className="px-6 py-4 border-b flex justify-between items-center rd-card-header">
              <h2 className={`text-lg font-semibold flex items-center gap-2 ${isDark ? 'text-gray-100' : 'text-gray-900'}`}><Activity className="w-5 h-5 text-yellow-500" />Job Status<span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{jobsStatus.length}</span></h2>
            </div>
            <div className="overflow-x-auto">
              {jobsStatus.length === 0
                ? <p className="text-center text-gray-400 py-14 text-sm">No jobs found.</p>
                : <table className="rd-table">
                  <thead><tr>
                    {['Job ID', 'Code File', 'Status', 'Progress', 'Created', 'Started', 'Completed', 'Error', 'Actions'].map(h =>
                      <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${isDark ? 'text-gray-300' : 'text-gray-500'}`}>{h}</th>
                    )}
                  </tr></thead>
                  <tbody className="divide-y divide-gray-50">
                    {jobsStatus.map((job, i) => {
                      const id = job.id || job._id || '';
                      const st = (job.status || '').toUpperCase();
                      const sc = st === 'COMPLETED' ? 'bg-green-100 text-green-700' : st === 'STARTED' || st === 'RUNNING' ? 'bg-yellow-100 text-yellow-700' : st === 'FAILED' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500';
                      const prog = st === 'COMPLETED' ? 100 : st === 'STARTED' || st === 'RUNNING' ? 60 : 0;
                      return <tr key={id || i} className={isDark ? 'hover:bg-gray-700 transition-colors' : 'hover:bg-yellow-50/50 transition-colors'}>
                        <td className="px-4 py-3"><code className="text-xs bg-yellow-50 text-yellow-700 px-2 py-1 rounded" title={id}>{id.slice(-10)}</code></td>
                        <td className="px-4 py-3"><code className="text-xs text-gray-500" title={job.code_file_id}>{(job.code_file_id || '').slice(-10)}</code></td>
                        <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-semibold ${sc}`}>{job.status}</span></td>
                        <td className="px-4 py-3"><div className="flex items-center gap-2"><div className="w-16 bg-gray-200 rounded-full h-1.5 overflow-hidden"><div className={`h-1.5 rounded-full transition-all ${st === 'COMPLETED' ? 'bg-green-500' : 'bg-yellow-400'}`} style={{ width: `${prog}%` }} /></div><span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{prog}%</span></div></td>
                        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{job.created_at ? new Date(job.created_at).toLocaleString() : '-'}</td>
                        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{job.started_at ? new Date(job.started_at).toLocaleString() : '-'}</td>
                        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{job.completed_at ? new Date(job.completed_at).toLocaleString() : '-'}</td>
                        <td className="px-4 py-3">{job.error_message ? <span className="text-xs text-red-500 bg-red-50 px-2 py-1 rounded">{job.error_message}</span> : <span className="text-xs text-green-400">—</span>}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            <button onClick={() => setDetailModal({ type: 'job', data: job })} className="rd-btn rd-btn-primary"><Eye className="w-3 h-3" />View</button>
                            <button onClick={() => { setNotifyForm({ title: '', message: '', related_id: id, related_type: 'job' }); setShowNotifyAdmin(true); }} className="flex items-center gap-1 px-2.5 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-xs font-medium transition"><MessageSquare className="w-3 h-3" />Notify</button>
                          </div>
                        </td>
                      </tr>;
                    })}
                  </tbody>
                </table>
              }
            </div>
          </div>
        )}

        {/* ── Explanations Tab ── */}
        {activeTab === 'explanations' && (
          <div className="space-y-6">
            {/* ── AI Explanations Table ── */}
            <div className="rd-card">
              <div className="px-6 py-4 border-b flex justify-between items-center">
                <h2 className={`text-lg font-semibold ${isDark ? 'text-gray-100' : 'text-gray-900'} flex items-center gap-2`}><MessageSquare className="w-5 h-5 text-purple-500" />AI Explanations<span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{explanations.length}</span></h2>
              </div>
              <div className="overflow-x-auto">
                {explanations.length === 0
                  ? <p className="text-center text-gray-400 py-10 text-sm">No explanations found.</p>
                  : <table className="rd-table">
                    <thead><tr>
                      {['Explanation ID', 'Analysis ID', 'Type', 'Created', 'Actions'].map(h =>
                        <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-gray-300' : 'text-gray-500'}`}>{h}</th>
                      )}
                    </tr></thead>
                    <tbody className="divide-y divide-gray-50">
                      {explanations.map(e => (
                        <tr key={e._id} className={isDark ? 'hover:bg-gray-700 transition-colors' : 'hover:bg-purple-50/40 transition-colors'}>
                          <td className="px-4 py-3"><code className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded" title={e._id}>{e._id.slice(-12)}</code></td>
                          <td className="px-4 py-3"><code className="text-xs text-gray-500" title={e.analysis_id}>{e.analysis_id.slice(-12)}</code></td>
                          <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-semibold ${e.explanation_type === 'high_level' ? 'bg-blue-100 text-blue-700' : 'bg-indigo-100 text-indigo-700'}`}>{e.explanation_type === 'high_level' ? 'High Level' : 'Low Level'}</span></td>
                          <td className="px-4 py-3 text-xs text-gray-500">{new Date(e.created_at).toLocaleString()}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1.5">
                              <button onClick={() => { setEvalModal({ id: e._id, type: 'explanation' }); setEvalScore('90'); setEvalComment(''); setEvalSuccess(false); }}
                                className="rd-btn rd-btn-primary">
                                <Star className="w-3 h-3" />Evaluate
                              </button>
                              <button onClick={() => { setNotifyForm({ title: '', message: '', related_id: e._id, related_type: 'explanation' }); setShowNotifyAdmin(true); }}
                                className="flex items-center gap-1 px-2.5 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-xs font-medium transition">
                                <MessageSquare className="w-3 h-3" />Notify
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                }
              </div>
            </div>
            <div className="rd-card">
              <div className="px-6 py-4 border-b flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-500" />AI Tasks
                  <span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{aiTasks.length}</span>
                </h2>
              </div>
              <div className="overflow-x-auto">
                {aiTasks.length === 0
                  ? <p className="text-center text-gray-400 py-10 text-sm">No AI tasks found.</p>
                  : <table className="rd-table">
                    <thead>
                      <tr>
                        {['Task ID', 'Analysis ID', 'Type', 'Status', 'Completed', 'Explanation ID', 'Content Preview'].map(h =>
                          <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${isDark ? 'text-gray-300' : 'text-gray-500'}`}>{h}</th>
                        )}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {aiTasks.map((t, i) => {
                        const st = (t.status || '').toLowerCase();
                        const sc = st === 'completed' ? 'bg-green-100 text-green-700' : st === 'failed' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700';
                        const expType = t.exp_type || t.result?.type || '';
                        const content_preview = t.result?.content ? t.result.content.slice(0, 80) + '…' : '—';
                        return <tr key={t._id || t.id || i} className={isDark ? 'hover:bg-gray-700 transition-colors' : 'hover:bg-indigo-50/40 transition-colors'}>
                          <td className="px-4 py-3"><code className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded" title={t.task_id}>{(t.task_id || '').slice(-12)}</code></td>
                          <td className="px-4 py-3"><code className="text-xs text-gray-500" title={t.analysis_id}>{(t.analysis_id || '').slice(-12)}</code></td>
                          <td className="px-4 py-3">
                            {expType && <span className={`px-2 py-1 rounded-full text-xs font-semibold ${expType === 'high_level' ? 'bg-blue-100 text-blue-700' : 'bg-indigo-100 text-indigo-700'}`}>
                              {expType === 'high_level' ? 'High Level' : 'Low Level'}
                            </span>}
                          </td>
                          <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-semibold ${sc}`}>{t.status || '—'}</span></td>
                          <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{t.completed_at ? new Date(t.completed_at).toLocaleString() : '-'}</td>
                          <td className="px-4 py-3"><code className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded" title={t.result?.explanation_id}>{(t.result?.explanation_id || '—').slice(-12)}</code></td>
                          <td className="px-4 py-3 max-w-xs"><span className="text-xs text-gray-500 line-clamp-2" title={t.result?.content}>{content_preview}</span></td>
                        </tr>;
                      })}
                    </tbody>
                  </table>
                }
              </div>
            </div>
          </div>
        )}

        {/* ── Generated Files Tab ── */}
        {activeTab === 'files' && (
          <div className="rd-card">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h2 className={`text-lg font-semibold ${isDark ? 'text-gray-100' : 'text-gray-900'} flex items-center gap-2`}><Eye className="w-5 h-5 text-green-500" />Generated Files<span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{generatedFiles.length}</span></h2>
            </div>
            <div className="overflow-x-auto">
              {generatedFiles.length === 0
                ? <p className="text-center text-gray-400 py-14 text-sm">No generated files found.</p>
                : <table className="rd-table">
                  <thead><tr>
                    {['Filename', 'Type', 'Size', 'Analysis ID', 'Project', 'Created', 'Downloads', 'Actions'].map(h =>
                      <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${isDark ? 'text-gray-300' : 'text-gray-500'}`}>{h}</th>
                    )}
                  </tr></thead>
                  <tbody className="divide-y divide-gray-50">
                    {generatedFiles.map(f => (
                      <tr key={f._id} className={isDark ? 'hover:bg-gray-700 transition-colors' : 'hover:bg-green-50/40 transition-colors'}>
                        <td className="px-4 py-3"><div className="flex items-center gap-2"><span className="text-base">{f.file_type === 'pdf' ? '📕' : '📄'}</span><span className="text-xs font-medium text-gray-700 max-w-xs truncate" title={f.filename}>{f.filename}</span></div></td>
                        <td className="px-4 py-3"><span className={`px-2 py-1 rounded text-xs font-bold uppercase ${f.file_type === 'pdf' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>{f.file_type}</span></td>
                        <td className="px-4 py-3 text-xs text-gray-500">{f.file_size ? (f.file_size / 1024).toFixed(1) + ' KB' : '—'}</td>
                        <td className="px-4 py-3"><code className="text-xs text-gray-400" title={f.analysis_id ?? ''}>{f.analysis_id ? String(f.analysis_id).slice(-10) : '—'}</code></td>
                        <td className="px-4 py-3"><code className="text-xs text-gray-400" title={f.project_id ?? ''}>{f.project_id ? String(f.project_id).slice(-10) : '—'}</code></td>
                        <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{f.created_at ? new Date(f.created_at).toLocaleString() : '—'}</td>
                        <td className="px-4 py-3"><span className="flex items-center gap-1 text-xs font-bold text-green-600"><svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>{f.downloaded_count ?? 0}</span></td>
                        <td className="px-4 py-3">
                          <button onClick={() => { setNotifyForm({ title: '', message: '', related_id: f._id, related_type: 'generated_file' }); setShowNotifyAdmin(true); }}
                            className="flex items-center gap-1 px-2.5 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-xs font-medium transition">
                            <MessageSquare className="w-3 h-3" />Notify
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              }
            </div>
          </div>
        )}

        {/* Statistics */}
        {activeTab === 'stats' && (
          <div className="space-y-6">
            {/* Toggle */}
            <div className={`border rounded-lg p-4 flex items-center justify-between transition-colors duration-300 ${isDark ? 'bg-blue-900/20 border-blue-800' : 'bg-blue-50 border-blue-200'}`}>
              <div className="flex items-center">
                <input type="checkbox" id="mock" checked={useMockData} onChange={e => setUseMockData(e.target.checked)} className="h-4 w-4 text-blue-600 border-gray-300 rounded" />
                <label htmlFor="mock" className={`ml-2 text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Use mock data for testing</label>
              </div>
              <span className="text-xs text-gray-500">{useMockData ? '🧪 Test values' : '📡 Live backend'}</span>
            </div>

            {/* Throughput */}
            <div className="rd-chart">
              <div className="flex justify-between items-center mb-5">
                <div className="flex items-center gap-3">
                  <div className="rd-chart-icon">
                    <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
                  </div>
                  <div><h3 className={`text-sm font-semibold ${isDark ? 'text-gray-100' : 'text-gray-800'}`}>Throughput (24h)</h3><p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Jobs processed per hour</p></div>
                </div>
                <div className="flex gap-2">
                  <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${isDark ? 'bg-blue-900/30 text-blue-300 border-blue-800' : 'bg-blue-50 text-blue-700 border-blue-100'}`}>⚡ {statsData?.throughput_24h ?? 0} jobs</span>
                  <span className="text-xs font-semibold px-3 py-1 rounded-full bg-gray-50 text-gray-600 border border-gray-100">⏱ {statsData?.avg_processing_time_ms ?? 0}ms avg</span>
                </div>
              </div>
              {statsData ? <ThroughputChart data={statsData} /> : <div className="animate-pulse bg-gray-100 rounded-xl" style={{ height: '180px' }} />}
            </div>

            {/* Queue Gauge */}
            <div className="rd-chart">
              <div className="flex justify-between items-center mb-5">
                <div className="flex items-center gap-3">
                  <div className="rd-chart-icon">
                    <svg className="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  </div>
                  <div><h3 className={`text-sm font-semibold ${isDark ? 'text-gray-100' : 'text-gray-800'}`}>Avg Queue Time</h3><p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Average wait time before processing</p></div>
                </div>
                <span className="text-2xl font-bold text-indigo-600">{statsData?.avg_queue_time_ms ?? 0}<span className="text-sm font-normal text-gray-400 ml-1">ms</span></span>
              </div>
              {statsData ? <QueueGauge data={statsData} /> : <div className="animate-pulse bg-gray-100 rounded-xl" style={{ height: '160px' }} />}
            </div>

            {/* All other cards — always render when statsData exists */}
            {statsData && <DurationByLanguageCard data={statsData.duration_by_language} isDark={isDark} />}
            {statsData && <ErrorClassificationCard errorData={statsData.error_classification} totalFailed={statsData.total_failed} isDark={isDark} />}
            {statsData && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <GeneratedFilesCard files={statsData.generated_files} isDark={isDark} />
                <SizeDistributionCard dist={statsData.size_distribution} isDark={isDark} />
              </div>
            )}
            {statsData && <CeleryHealthCard celeryData={{ active_tasks: statsData.active_tasks, reserved_tasks: statsData.reserved_tasks, retried_tasks: statsData.retried_tasks, celery_status: statsData.celery_status }} isDark={isDark} />}
            {statsData && <VerifierStatsCard byType={statsData.verifier_by_type} overall={statsData.verifier_overall} isDark={isDark} />}
            {evalStats && <EvalStatsCard evalData={evalStats} isDark={isDark} />}
          </div>
        )}

        {/* Evaluations tab — shows evaluation history */}
        {activeTab === 'evaluations' && (
          <div className={`rd-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
            <div className={`px-6 py-4 border-b flex justify-between items-center ${isDark ? 'border-gray-700' : ''}`}>
              <h2 className={`text-lg font-semibold flex items-center gap-2 ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
                <Star className="w-5 h-5 text-yellow-500" />
                Evaluation History
                <span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{evaluationHistory.length}</span>
              </h2>
              <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                {evaluationHistory.filter(e => e.evaluation !== null).length} evaluated · {evaluationHistory.filter(e => e.evaluation === null).length} pending
              </span>
            </div>
            <div className="p-6">
              {evaluationHistory.length === 0
                ? <div className="text-center py-12"><Star className="w-10 h-10 text-gray-200 mx-auto mb-3" /><p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>No explanations found.</p></div>
                : <div className="space-y-4">
                  {evaluationHistory.map((item) => {
                    const ev = item.evaluation;
                      const pct = ev ? Math.min(ev.final_percentage, 100) : 0;
                    const verdictColors: Record<string, string> = { EXCELLENT: '#10b981', GOOD: '#3b82f6', ACCEPTABLE: '#f59e0b', POOR: '#ef4444' };
                    const scoreColor = ev ? (verdictColors[ev.verdict] || '#6b7280') : '#9ca3af';
                    const scoreBg = ev ? (
                      ev.verdict === 'EXCELLENT' ? (isDark ? 'rgba(16,185,129,.12)' : 'rgba(16,185,129,.08)') :
                      ev.verdict === 'GOOD' ? (isDark ? 'rgba(59,130,246,.12)' : 'rgba(59,130,246,.08)') :
                      ev.verdict === 'ACCEPTABLE' ? (isDark ? 'rgba(245,158,11,.12)' : 'rgba(245,158,11,.08)') :
                      (isDark ? 'rgba(239,68,68,.12)' : 'rgba(239,68,68,.08)')
                    ) : (isDark ? 'rgba(156,163,175,.08)' : 'rgba(156,163,175,.06)');
                    const layerLabels: Record<string, string> = {
                      ast_cross_check: 'AST', completeness: 'Complete',
                      llm_judge: 'LLM', human_review: 'Human'
                    };
                    return (
                      <div key={item.explanation_id} className={`rounded-xl border p-4 transition-colors ${isDark ? 'border-gray-700 hover:bg-gray-700/50' : 'border-gray-100 hover:bg-gray-50/60'}`}
                        style={{ boxShadow: isDark ? 'none' : '0 1px 4px rgba(0,0,0,.04)' }}>
                        <div className="flex items-start justify-between gap-4 flex-wrap">
                          {/* Left: explanation info */}
                          <div className="flex items-start gap-3 min-w-0 flex-1">
                            <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${item.exp_type === 'high_level' ? 'bg-blue-100' : 'bg-indigo-100'}`}>
                              <MessageSquare className={`w-4 h-4 ${item.exp_type === 'high_level' ? 'text-blue-600' : 'text-indigo-600'}`} />
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2 flex-wrap mb-1">
                                <code className={`text-xs px-2 py-0.5 rounded font-mono ${isDark ? 'bg-purple-900/40 text-purple-300' : 'bg-purple-50 text-purple-700'}`} title={item.explanation_id}>{item.explanation_id.slice(-14)}</code>
                                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${item.exp_type === 'high_level' ? 'bg-blue-100 text-blue-700' : 'bg-indigo-100 text-indigo-700'}`}>
                                  {item.exp_type === 'high_level' ? 'High Level' : 'Low Level'}
                                </span>
                                {ev && <span className="px-2 py-0.5 rounded-full text-xs font-bold" style={{ background: scoreBg, color: scoreColor }}>{ev.verdict}</span>}
                              </div>
                              <p className={`text-xs line-clamp-2 mb-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{item.content?.slice(0, 120)}…</p>
                              <div className={`text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{new Date(item.created_at).toLocaleString()}</div>
                            </div>
                          </div>
                          {/* Right: score or review button */}
                          <div className="flex items-center gap-3 flex-shrink-0">
                            {ev ? (
                              <div className="flex flex-col items-end gap-2">
                                <div className="flex items-baseline gap-1 px-3 py-1.5 rounded-lg" style={{ background: scoreBg, border: `1px solid ${scoreColor}33` }}>
                                  <span style={{ fontSize: '20px', fontWeight: '800', color: scoreColor }}>{pct.toFixed(1)}</span>
                                  <span style={{ fontSize: '12px', color: scoreColor, opacity: 0.7 }}>/100</span>
                                </div>
                                <button
                                  onClick={() => { setEvalModal({ id: item.explanation_id, type: 'explanation', content: item.content }); setEvalScore(String(Math.round(ev.layer_scores?.human_review ? ev.layer_scores.human_review * 100 : pct))); setEvalComment(''); setEvalSuccess(false); }}
                                  className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                                >
                                  <Star className="w-3 h-3" />Re-evaluate
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() => { setEvalModal({ id: item.explanation_id, type: 'explanation', content: item.content }); setEvalScore('90'); setEvalComment(''); setEvalSuccess(false); }}
                                className="flex items-center gap-1.5 px-3 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-xs font-semibold"
                              >
                                <Star className="w-3.5 h-3.5" />Review
                              </button>
                            )}
                          </div>
                        </div>
                        {/* Layer scores breakdown */}
                        {ev && ev.layer_scores && (
                          <div className={`mt-3 pt-3 border-t ${isDark ? 'border-gray-700' : 'border-gray-100'}`}>
                            <div className="grid grid-cols-4 gap-2">
                              {Object.entries(ev.layer_scores).map(([key, val]) => {
                                const v = typeof val === 'number' ? val : 0;
                                const norm = Math.min(v, 1);
                                const lc = norm >= 0.7 ? '#10b981' : norm >= 0.5 ? '#f59e0b' : '#ef4444';
                                return (
                                  <div key={key} className={`rounded-lg p-2 text-center ${isDark ? 'bg-gray-700/60' : 'bg-gray-50'}`}>
                                    <div style={{ fontSize: '13px', fontWeight: '700', color: lc }}>{(v * 100).toFixed(0)}</div>
                                    <div style={{ fontSize: '10px', color: isDark ? '#6b7280' : '#9ca3af', marginTop: '1px' }}>{layerLabels[key] || key}</div>
                                  </div>
                                );
                              })}
                            </div>
                            <div className={`text-xs mt-2 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                              Evaluated {new Date(ev.evaluated_at).toLocaleString()}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              }
            </div>
          </div>
        )}

      </main>

      {/* ── Modals ── */}
      <div>
      {evalModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" style={{ animation: 'backdropIn .2s ease-out both' }} onClick={() => setEvalModal(null)}>
          <div className={`rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto transition-colors ${isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white'}`} onClick={e => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Evaluate Explanation</h3>
                <button onClick={() => setEvalModal(null)} className={`text-gray-400 hover:text-gray-700 ${isDark ? 'text-white' : 'text-gray-900'} rounded-lg w-8 h-8 flex items-center justify-center transition`}>✕</button>
              </div>

              {/* Explanation Content */}
              <div className="bg-gray-50 rounded-lg px-4 py-3 mb-4">
                <div className={`text-sm text-gray-600 ${isDark ? 'text-gray-200' : 'text-gray-800'} max-h-40 overflow-y-auto bg-gray-50 rounded p-3`}>
                  {evalModal.content || 'No content available'}
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Score (0 – 100)</label>
                <div className="flex items-center gap-3">
                  <input type="range" min="0" max="100" step="1" value={evalScore}
                    onChange={e => setEvalScore(e.target.value)}
                    className="flex-1 h-2 rounded-full accent-yellow-500" />
                  <span className="text-lg font-bold text-yellow-600 min-w-16 text-right">{parseInt(evalScore)}<span className="text-sm font-normal text-gray-400">/100</span></span>
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1"><span>0 — Poor</span><span>100 — Excellent</span></div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Comment</label>
                <textarea value={evalComment} onChange={e => setEvalComment(e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-300 transition-colors ${isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-200 text-gray-900'}`}
                  rows={3} placeholder="e.g. Very clear and comprehensive explanation" />
              </div>
              {evalSuccess && <div className="bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 text-sm flex items-center gap-2"><CheckCircle className="w-4 h-4" />Submitted successfully!</div>}
              <div className="px-6 pb-6 flex gap-3 justify-end">
                <button onClick={() => setEvalModal(null)} className="rd-btn rd-btn-secondary px-4 py-2">Cancel</button>
                <button disabled={evalSubmitting} onClick={async () => {
                  setEvalSubmitting(true);
                  try {
                    const explanationId = evalModal?.id;
                    if (!explanationId) { console.error('No explanation ID'); setEvalSubmitting(false); return; }
                    // API expects score as 0-1 float, convert from 0-100
                    await apiClient.post(`/api/analysis/submit-human-review/${explanationId}/`, { score: parseInt(evalScore) / 100, comment: evalComment });
                    setEvalSuccess(true);
                    // Refresh evalHistory after successful submission
                    try {
                      const eh = await apiClient.get('/api/analysis/evaluation-history/');
                      const ehd = eh.data;
                      const items: ExplanationEvaluation[] = Array.isArray(ehd) ? ehd : ehd?.explanations || [];
                      setEvaluationHistory(items);
                    } catch (e) { console.error('Failed to refresh evaluation history:', e); }
                    setTimeout(() => setEvalModal(null), 1500);
                  } catch (e) { console.error(e); }
                  setEvalSubmitting(false);
                }} className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition text-sm font-medium disabled:opacity-50">
                  {evalSubmitting ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Star className="w-4 h-4" />}
                  Submit
                </button>
              </div>
            </div>
          </div>
        </div>
        )}

        {/* ── Change Password Modal ── */}
        {showChangePwd && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowChangePwd(false)}>
            <div className={`rounded-2xl shadow-2xl w-full max-w-md transition-colors ${isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white'}`} style={{ animation: 'modalSlideUp .25s ease-out both' }} onClick={e => e.stopPropagation()}>
              <div className={`flex items-center justify-between px-6 py-4 border-b ${isDark ? 'border-gray-700' : ''}`}>
                <h3 className={`text-base font-bold flex items-center gap-2 ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
                  <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
                  Change Password
                </h3>
                <button onClick={() => setShowChangePwd(false)} className="text-gray-400 hover:text-gray-700 w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition text-lg">✕</button>
              </div>
              <div className="p-6 space-y-4">
                {(['old_password', 'new_password', 'confirm_new_password'] as const).map(field => (
                  <div key={field}>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                      {field === 'old_password' ? 'Current Password' : field === 'new_password' ? 'New Password' : 'Confirm New Password'}
                    </label>
                    <input type="password" value={pwdForm[field]}
                      onChange={e => setPwdForm({ ...pwdForm, [field]: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors ${isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500' : 'border-gray-200 text-gray-900'}`}
                      placeholder={field === 'old_password' ? 'Current password' : 'New password'} />
                  </div>
                ))}
                {pwdError && <div className="bg-red-50 border border-red-200 text-red-600 rounded-lg px-4 py-3 text-sm">{pwdError}</div>}
                {pwdSuccess && <div className="bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 text-sm flex items-center gap-2"><CheckCircle className="w-4 h-4" />Password changed successfully!</div>}
              </div>
              <div className="px-6 pb-6 flex gap-3 justify-end">
                <button onClick={() => setShowChangePwd(false)} className="rd-btn rd-btn-secondary px-4 py-2">Cancel</button>
                <button disabled={pwdSubmitting} onClick={async () => {
                  if (pwdForm.new_password !== pwdForm.confirm_new_password) { setPwdError('Passwords do not match'); return; }
                  if (pwdForm.new_password.length < 8) { setPwdError('Password must be at least 8 characters'); return; }
                  setPwdSubmitting(true); setPwdError('');
                  try {
                    await apiClient.post('/api/upm/account/change-password/', pwdForm);
                    setPwdSuccess(true);
                    setTimeout(() => setShowChangePwd(false), 1500);
                  } catch (e: any) { setPwdError(e?.response?.data?.message || e?.response?.data?.error || 'Failed to change password'); }
                  setPwdSubmitting(false);
                }} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium disabled:opacity-50">
                  {pwdSubmitting ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                  Change Password
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewerDashboard;