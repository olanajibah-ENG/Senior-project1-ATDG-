import React, { createContext, useContext, useEffect, useState } from 'react';
import { i18n } from '../utils/i18n';
import type { Language } from '../utils/i18n';

interface LanguageContextType {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: string, params?: { [key: string]: any }) => string;
  isRTL: boolean;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

interface LanguageProviderProps {
  children: React.ReactNode;
}

// Read language synchronously before first render — prevents flash/wrong state
// Only supports 'en' and 'ar' — no fallback to French/Spanish
const getInitialLanguage = (): Language => {
  try {
    const saved = localStorage.getItem('language') as Language | null;
    if (saved === 'ar' || saved === 'en') return saved;
  } catch (e) {
    console.warn('Failed to read language from localStorage', e);
  }
  return 'en';
};

const applyDocumentLang = (lang: Language) => {
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  document.documentElement.lang = lang;
};

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(getInitialLanguage);
  const [isRTL, setIsRTL] = useState<boolean>(getInitialLanguage() === 'ar');

  const setLanguage = (newLanguage: Language) => {
    // Enforce only 'en' or 'ar' — reject any other value
    const validLang: Language = newLanguage === 'ar' ? 'ar' : 'en';
    try {
      i18n.setLanguage(validLang);
      localStorage.setItem('language', validLang);
      setLanguageState(validLang);
      setIsRTL(validLang === 'ar');
      applyDocumentLang(validLang);
    } catch (e) {
      console.error('Failed to change language', e);
    }
  };

  const t = (key: string, params?: { [key: string]: any }) => {
    return i18n.t(key, params) || key;
  };

  // Sync i18n instance and document on mount
  useEffect(() => {
    const initialLang = getInitialLanguage();
    i18n.setLanguage(initialLang);
    applyDocumentLang(initialLang);
    setIsRTL(initialLang === 'ar');
  }, []);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, isRTL }}>
      {children}
    </LanguageContext.Provider>
  );
};
