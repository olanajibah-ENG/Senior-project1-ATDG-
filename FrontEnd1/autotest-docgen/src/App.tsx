// App.tsx
// 🚨 إزالة الاستيراد لـ BrowserRouter كـ Router
import { Routes, Route } from 'react-router-dom'; // 👈 ترك Routes و Route فقط
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast/Toast';

import Home from './Home';
import PremiumAuth from './PremiumAuth';
import Dashboard from './Dashboard';
import UsersList from './compoents/ProjectCutomizationModal/UsersList';
import AnalysisResultPage from './AnalysisResultPage';
import ClassDiagramPage from './ClassDiagramPage';
import LogicExplanationResultPage from './LogicExplanationResultPage';
import DocumentGenerationPage from './DocumentGenerationPage';
import GeneratedFilesPage from './GeneratedFilesPage';
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
          <Route path="/users" element={<UsersList users={[]} isLoading={false} error={null} />} />
          <Route path="/analysis" element={<AnalysisResultPage />} />
          <Route path="/diagram" element={<ClassDiagramPage />} />
          <Route path="/logic-explanation-result" element={<LogicExplanationResultPage />} />
          <Route path="/document-generation" element={<DocumentGenerationPage />} />
          <Route path="/generated-files" element={<GeneratedFilesPage />} />
          {/* يمكن إضافة مسارات أخرى هنا */}
        </Routes>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;