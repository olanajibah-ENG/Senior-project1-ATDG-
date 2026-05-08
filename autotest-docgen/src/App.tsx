// App.tsx
// إزالة الاستيراد لـ BrowserRouter كـ Router
import { Routes, Route } from 'react-router-dom'; // ترك Routes و Route فقط
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast/Toast';

import Home from './Home';
import PremiumAuth from './PremiumAuth';
import Dashboard from './Dashboard';
import AdminDashboard from './components/AdminDashboard';
import ReviewerDashboard from './components/ReviewerDashboard';
import RoleGuard from './components/RoleGuard';
import UsersList from './compoents/ProjectCutomizationModal/UsersList';
import AnalysisResultPage from './AnalysisResultPage';
import ClassDiagramPage from './ClassDiagramPage';
import LogicExplanationResultPage from './LogicExplanationResultPage';
import DocumentGenerationPage from './DocumentGenerationPage';
import GeneratedFilesPage from './GeneratedFilesPage';
import ProjectFilesPage from './ProjectFilesPage';
import ProjectTreePage from './ProjectTreePage';
// يجب عليك إنشاء وإضافة ملفات الـ contextes هنا إذا كنت تستخدم useAuth

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
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

          <Route path="/users" element={<UsersList users={[]} isLoading={false} error={null} />} />
          <Route path="/analysis" element={<AnalysisResultPage />} />
          <Route path="/diagram" element={<ClassDiagramPage />} />
          <Route path="/logic-explanation-result" element={<LogicExplanationResultPage />} />
          <Route path="/document-generation" element={<DocumentGenerationPage />} />
          <Route path="/generated-files" element={<GeneratedFilesPage />} />
          <Route path="/dashboard/projects/:project_id/files" element={<ProjectFilesPage />} />
          <Route path="/dashboard/projects/:project_id/tree" element={<ProjectTreePage />} />
          {/* يمكن إضافة مسارات أخرى هنا */}
        </Routes>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;