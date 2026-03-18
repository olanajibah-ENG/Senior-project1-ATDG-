import React, { createContext, useContext, useEffect, useState } from 'react';
import { i18n } from '../utils/i18n';
import type { Language } from '../utils/i18n';

interface LanguageContextType {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: string, params?: { [key: string]: any }) => string;
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

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>('en');

  const setLanguage = (newLanguage: Language) => {
    i18n.setLanguage(newLanguage);
    setLanguageState(newLanguage);
  };

  const t = (key: string, params?: { [key: string]: any }) => {
    return i18n.t(key, params);
  };

  useEffect(() => {
    i18n.init();
    setLanguageState(i18n.getLanguage());
  }, []);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};