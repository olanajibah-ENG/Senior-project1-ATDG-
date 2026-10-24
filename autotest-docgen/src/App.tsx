// App.tsx
// إزالة الاستيراد لـ BrowserRouter كـ Router
import { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom'; // ترك Routes و Route فقط
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast/Toast';
import LoadingSpinner from './components/ProjectCustomizationModal/LoadingSpinner';
import RoleGuard from './components/RoleGuard';

// كل صفحات الـRoutes بتنحمّل بشكل كسول (lazy) بدل ما تنحمّل كلها مع أول تحميل للموقع.
// هيك المتصفح بيجيب فقط كود الصفحة يلي المستخدم فعلياً فاتحها.
const Home = lazy(() => import('./Home'));
const PremiumAuth = lazy(() => import('./PremiumAuth'));
const Dashboard = lazy(() => import('./Dashboard'));
const AdminDashboard = lazy(() => import('./components/AdminDashboard'));
const ReviewerDashboard = lazy(() => import('./components/ReviewerDashboard'));
const AnalysisResultPage = lazy(() => import('./AnalysisResultPage'));
const ClassDiagramPage = lazy(() => import('./ClassDiagramPage'));
const LogicExplanationResultPage = lazy(() => import('./LogicExplanationResultPage'));
const DocumentGenerationPage = lazy(() => import('./DocumentGenerationPage'));
const GeneratedFilesPage = lazy(() => import('./GeneratedFilesPage'));
const ProjectFilesPage = lazy(() => import('./ProjectFilesPage'));
const ProjectTreePage = lazy(() => import('./ProjectTreePage'));
const ProjectCodesPage = lazy(() => import('./ProjectCodesPage'));
const ProjectDocumentsPage = lazy(() => import('./ProjectDocumentsPage'));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'));
// يجب عليك إنشاء وإضافة ملفات الـ contextes هنا إذا كنت تستخدم useAuth

// شاشة تحميل بسيطة تظهر لحظة تحميل أي صفحة (Suspense fallback)
const PageFallback = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
    <LoadingSpinner size="large" message="جاري تحميل الصفحة..." />
  </div>
);

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            {/* الواجهة الأولى: صفحة Home تفاعلية */}
            <Route path="/" element={<Home />} />
            {/* واجهة تسجيل الدخول / إنشاء حساب */}
            <Route path="/auth" element={<PremiumAuth />} />

            {/* الواجهة الثانية: لوحة التحكم وإدارة المشاريع */}
            <Route path="/dashboard" element={<Dashboard />} />

            {/* Admin Dashboard - Protected Route */}
            <Route
              path="/admin"
              element={
                <RoleGuard allowedRoles={['admin']}>
                  <AdminDashboard />
                </RoleGuard>
              }
            />

            {/* Reviewer Dashboard - Protected Route */}
            <Route
              path="/reviewer"
              element={
                <RoleGuard allowedRoles={['reviewer']}>
                  <ReviewerDashboard />
                </RoleGuard>
              }
            />

            <Route path="/analysis" element={<AnalysisResultPage />} />
            <Route path="/diagram" element={<ClassDiagramPage />} />
            <Route path="/logic-explanation-result" element={<LogicExplanationResultPage />} />
            <Route path="/document-generation" element={<DocumentGenerationPage />} />
            <Route path="/generated-files" element={<GeneratedFilesPage />} />
            <Route path="/dashboard/projects/:project_id/files" element={<ProjectFilesPage />} />
            <Route path="/dashboard/projects/:project_id/tree" element={<ProjectTreePage />} />
            <Route path="/dashboard/projects/:project_id/codes" element={<ProjectCodesPage />} />
            <Route path="/dashboard/projects/:project_id/documents" element={<ProjectDocumentsPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            {/* يمكن إضافة مسارات أخرى هنا */}
          </Routes>
        </Suspense>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
