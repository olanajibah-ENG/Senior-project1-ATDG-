import { useLanguage } from '../context/LanguageContext'

export function LanguageSelector() {
  const { language, setLanguage } = useLanguage()

  return (
    <button
      onClick={() => setLanguage(language === 'en' ? 'ar' : 'en')}
      className="language-selector-btn unified-theme-toggle"
      style={{ width: '44px', fontSize: '11px', fontWeight: 700, letterSpacing: '0.03em' }}
      title={language === 'en' ? 'Switch to Arabic' : 'Switch to English'}
    >
      {language === 'en' ? 'AR' : 'EN'}
    </button>
  )
}
