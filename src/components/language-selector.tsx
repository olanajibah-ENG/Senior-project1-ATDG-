import { Languages } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { Button } from './ui/Button'
import { useState } from 'react'

export function LanguageSelector() {
  const { language, setLanguage } = useLanguage()
  const [isOpen, setIsOpen] = useState(false)

  const languages = [
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'ar', name: 'العربية', flag: '🇸🇦' },
    { code: 'fr', name: 'Français', flag: '🇫🇷' },
    { code: 'es', name: 'Español', flag: '🇪🇸' },
  ]

  const currentLanguage = languages.find(lang => lang.code === language) || languages[0]

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-50 bg-white/10 dark:bg-black/20 border border-white/20 dark:border-white/10 backdrop-blur-sm text-white dark:text-gray-100 hover:bg-white/20 dark:hover:bg-black/30"
      >
        <Languages className="h-[1.2rem] w-[1.2rem] mr-2" />
        <span className="text-sm">{currentLanguage.flag} {currentLanguage.name}</span>
      </Button>

      {isOpen && (
        <div className="fixed top-16 left-4 z-50 bg-white/95 dark:bg-black/95 backdrop-blur-md border border-white/20 dark:border-white/10 rounded-lg shadow-lg min-w-[150px]">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                setLanguage(lang.code as any)
                setIsOpen(false)
              }}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center space-x-2 ${
                language === lang.code ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              <span>{lang.flag}</span>
              <span>{lang.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
