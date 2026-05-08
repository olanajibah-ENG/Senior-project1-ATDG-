import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'; // 👈 استيراد BrowserRouter
import './index.css'
import App from './App.tsx'
// 🚨 تأكدي من مسار الاستيراد الصحيح للـ Providers
import { AuthProvider } from './context/AuthContext.tsx'
import { LanguageProvider } from './context/LanguageContext.tsx'
import { ThemeProvider } from './components/theme-provider'

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {/* 🚨 الآن BrowserRouter هو الغلاف الخارجي */}
    <BrowserRouter>
      <ThemeProvider defaultTheme="system" storageKey="ui-theme">
        <LanguageProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </LanguageProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
);