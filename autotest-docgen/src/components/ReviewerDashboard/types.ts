// أنواع مشتركة بين ReviewerDashboard.tsx وكومبوننتات الرسوم البيانية الفرعية
// (تم فصلها هون بدل ما تتكرر بكل ملف — راجع الخطوة ٧ من التحسينات)

export interface EvalStatsData {
  total_evaluations: number; average_score: number;
  verdict_distribution: Array<{ _id: string; count: number }>;
}

export interface StatsData {
  throughput_24h: number; avg_processing_time_ms: number; avg_queue_time_ms: number;
  active_tasks: number; total_explanations: number; reserved_tasks: number;
  retried_tasks: number; celery_status: string;
  duration_by_language: Record<string, { avg_duration_ms: number; count: number }>;
  error_classification: Record<string, number>; total_failed: number;
  size_distribution: { under_50KB: number; '50_to_200KB': number; over_200KB: number };
  generated_files: Record<string, { count: number; avg_size_bytes: number; max_size_bytes: number; total_downloads: number }>;
  verifier_by_type: Record<string, { total: number; verifier_success: number; verifier_fallbacks: number; fallback_rate_percent: number }>;
  verifier_overall: { total_explanations: number; verifier_fallbacks: number; fallback_rate_percent: number };
}
