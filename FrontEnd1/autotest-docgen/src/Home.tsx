import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Code2, FileText, GitBranch, Moon, Sun, Globe} from 'lucide-react';
import { i18n } from './utils/i18n';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [currentLang, setCurrentLang] = useState<'EN' | 'AR'>('EN');

  // Initialize i18n on component mount
  useEffect(() => {
    // Set current lang state based on i18n
    setCurrentLang(i18n.getLanguage() === 'ar' ? 'AR' : 'EN');
  }, []);

  // Handle language change
  const handleLanguageChange = () => {
    const newLang = currentLang === 'EN' ? 'AR' : 'EN';
    setCurrentLang(newLang);
    // Update i18n language
    i18n.setLanguage(newLang === 'AR' ? 'ar' : 'en');
  };

  // Generate stable particles and lines on mount only
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; delay: number; duration: number }>>([]);
  const [lines, setLines] = useState<Array<{ id: number; x: number; y: number; rotation: number; delay: number }>>([]);

  useEffect(() => {
    // Generate particles once
    const newParticles = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 10,
      duration: 15 + Math.random() * 10
    }));
    setParticles(newParticles);

    // Generate lines once
    const newLines = Array.from({ length: 5 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      rotation: Math.random() * 360,
      delay: Math.random() * 5
    }));
    setLines(newLines);
  }, []);

  // Apply dark mode class to body
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [isDarkMode]);

  return (
    <div className={`premium-hero ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      {/* Animated Background */}
      <div className="animated-bg">
        <div className="floating-particles">
          {particles.map((particle) => (
            <div
              key={particle.id}
              className="particle"
              style={{
                left: `${particle.x}%`,
                animationDelay: `${particle.delay}s`,
                animationDuration: `${particle.duration}s`
              }}
            />
          ))}
        </div>
        <div className="geometric-lines">
          {lines.map((line) => (
            <div
              key={line.id}
              className="geo-line"
              style={{
                left: `${line.x}%`,
                top: `${line.y}%`,
                transform: `rotate(${line.rotation}deg)`,
                animationDelay: `${line.delay}s`
              }}
            />
          ))}
        </div>
      </div>

      {/* Glassmorphism Header */}
      <motion.header
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className={`fixed top-0 left-0 right-0 z-50 backdrop-blur-md border-b ${isDarkMode
          ? 'bg-black/20 border-white/10'
          : 'bg-white/80 border-gray-200/50'
          }`}
      >
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3, duration: 0.6 }}
              className="flex items-center gap-3"
            >
              <Code2 size={32} className={`${isDarkMode ? 'text-white' : 'text-purple-600'} drop-shadow-lg`} />
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.8 }}
                className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-800'} drop-shadow-lg`}
              >
                &lt;/&gt; AutoTest & DocGen
              </motion.span>
            </motion.div>

            <motion.nav
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7, duration: 0.6 }}
              className="flex items-center gap-4"
            >
              {/* Language Toggle */}
              <button
                onClick={handleLanguageChange}
                className={`px-3 py-1.5 rounded-full border text-sm font-medium transition-all duration-300 backdrop-blur-sm ${isDarkMode
                  ? 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                  : 'bg-purple-100/50 border-purple-200/50 text-purple-700 hover:bg-purple-200/50'
                  }`}
              >
                <Globe className="w-4 h-4 inline mr-1" />
                {currentLang === 'EN' ? 'EN' : 'عربي'}
              </button>

              {/* Theme Toggle */}
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                className={`p-2 rounded-lg border transition-all duration-300 backdrop-blur-sm ${isDarkMode
                  ? 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                  : 'bg-gray-100/50 border-gray-200/50 text-gray-700 hover:bg-gray-200/50'
                  }`}
              >
                {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>

              
            </motion.nav>
          </div>
        </div>
      </motion.header>

      {/* Hero Section */}
      <main className="pt-32 pb-20 px-6">
        <motion.section
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="max-w-7xl mx-auto text-center mb-20"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6, duration: 0.6 }}
            className="mb-8"
          >
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.8 }}
              className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black leading-tight mb-6"
            >
              <span font-style:Bold className={`bg-gradient-to-r bg-clip-text text-transparent drop-shadow-2xl ${isDarkMode
                ? 'from-purple-100 via-pink-100 to-purple-100'
                : 'from-purple-600 via-pink-600 to-purple-600'
                }`}>
                {currentLang === 'EN' ? 'Transform Your Code with AI-Powered Analysis' : 'حول كودك باستخدام التحليل المعزز بالذكاء الاصطناعي'}
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.0, duration: 0.8 }}
              className={`text-xl sm:text-2xl md:text-3xl font-medium max-w-3xl mx-auto leading-relaxed drop-shadow-lg ${isDarkMode ? 'text-gray-100' : 'text-gray-700'
                }`} style={{ textShadow: isDarkMode ? '0 2px 12px rgba(0,0,0,0.8)' : '0 1px 4px rgba(0,0,0,0.1)' }}
            >
              {currentLang === 'EN' ? 'Cut code review time by 70% with AI-powered analysis, diagrams & docs' : 'قلل وقت مراجعة الكود بنسبة 70% باستخدام التحليل المعزز بالذكاء الاصطناعي، المخططات والوثائق'}
            </motion.p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2, duration: 0.6 }}
            className="flex justify-center"
          >
            <motion.button
              whileHover={{ scale: 1.05, y: -3 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate('/auth')}
              className={`group px-8 py-4 text-lg font-bold rounded-xl shadow-2xl transition-all duration-300 flex items-center gap-3 ${isDarkMode
                ? 'bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white hover:shadow-purple-500/50 hover:brightness-110'
                : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-purple-400/50 hover:brightness-105'
                }`}
              style={{
                boxShadow: isDarkMode
                  ? '0 20px 40px rgba(147, 51, 234, 0.4)'
                  : '0 15px 35px rgba(147, 51, 234, 0.3)'
              }}
            >
              <span>{currentLang === 'EN' ? 'GET STARTED NOW' : 'ابدأ الآن'}</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </motion.button>
          </motion.div>
        </motion.section>

        {/* Stats Row */}
        <motion.section
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.4, duration: 0.8 }}
          className="max-w-4xl mx-auto mb-20"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 1.6, duration: 0.6 }}
              className={`backdrop-blur-sm border rounded-xl p-8 text-center transition-all duration-300 ${isDarkMode
                ? 'bg-gray-900/60 border-white/20 hover:bg-gray-900/70'
                : 'bg-white/60 border-gray-200/50 hover:bg-white/80'
                }`}
            >
              <div className={`text-4xl font-black mb-2 ${isDarkMode ? 'text-white' : 'text-gray-800'
                }`} style={{ textShadow: isDarkMode ? '0 3px 12px rgba(0,0,0,0.9)' : '0 1px 4px rgba(0,0,0,0.1)' }}>500+</div>
              <div className={`font-medium ${isDarkMode ? 'text-wh' : 'text-gray-600' 
                }`} style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0,0,0,0.9)' : '0 1px 4px rgba(0,0,0,0.1)' }}>
                {currentLang === 'EN' ? 'Developers' : 'المطورون'}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 1.7, duration: 0.6 }}
              className={`backdrop-blur-sm border rounded-xl p-8 text-center transition-all duration-300 ${isDarkMode
                ? 'bg-gray-900/60 border-white/20 hover:bg-gray-900/70'
                : 'bg-white/60 border-gray-200/50 hover:bg-white/80'
                }`}
            >
              <div className={`text-4xl font-black mb-2 ${isDarkMode ? 'text-white' : 'text-gray-800'
                }`} style={{ textShadow: isDarkMode ? '0 3px 12px rgba(0,0,0,0.9)' : '0 1px 4px rgba(0,0,0,0.1)' }}>10k+</div>
              <div className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-600'
                }`} style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0,0,0,0.7)' : 'none' }}>
                {currentLang === 'EN' ? 'Diagrams Generated' : 'المخططات المولدة'}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 1.8, duration: 0.6 }}
              className={`backdrop-blur-sm border rounded-xl p-8 text-center transition-all duration-300 ${isDarkMode
                ? 'bg-gray-900/60 border-white/20 hover:bg-gray-900/70'
                : 'bg-white/60 border-gray-200/50 hover:bg-white/80'
                }`}
            >
              <div className={`text-4xl font-black mb-2 ${isDarkMode ? 'text-white' : 'text-gray-800'
                }`} style={{ textShadow: isDarkMode ? '0 3px 12px rgba(0,0,0,0.9)' : '0 1px 4px rgba(0,0,0,0.1)' }}>99.9%</div>
              <div className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-600'
                }`} style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0,0,0,0.7)' : 'none' }}>
                {currentLang === 'EN' ? 'Uptime' : 'وقت التشغيل'}
              </div>
            </motion.div>
          </div>
        </motion.section>

        {/* Features Grid */}
        <motion.section
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 2.0, duration: 0.8 }}
          className="max-w-6xl mx-auto mb-20"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8" >
            {[
              {
                icon: <Code2 size={32} color={isDarkMode ? 'white' : 'black'} />,
                title: currentLang === 'EN' ? "AI-Powered Analysis" : "التحليل المعزز بالذكاء الاصطناعي",
                description: currentLang === 'EN'
                  ? "Deep code understanding with advanced AI algorithms that analyze your codebase for patterns, bugs, and optimization opportunities."
                  : "فهم عميق للكود باستخدام خوارزميات ذكاء اصطناعي متقدمة تحلل قاعدة الكود الخاصة بك للبحث عن الأنماط والأخطاء وفرص التحسين."
              },
              {
                icon: <FileText size={32} color={isDarkMode ? 'white' : 'black'} />,
                title: currentLang === 'EN' ? "Smart Documentation" : "التوثيق الذكي",
                description: currentLang === 'EN'
                  ? "Auto-generate comprehensive technical documentation from your codebase with intelligent context-aware descriptions and examples."
                  : "توليد تلقائي لوثائق تقنية شاملة من قاعدة الكود الخاصة بك مع أوصاف وأمثلة ذكية تتناسب مع السياق."
              },
              {
                icon: <GitBranch size={32} color={isDarkMode ? 'white' : 'black'}  />,
                title: currentLang === 'EN' ? "Visual Diagrams" : "المخططات المرئية",
                description: currentLang === 'EN'
                  ? "Create beautiful class diagrams, flowcharts, and architecture visualizations that make complex systems easy to understand."
                  : "إنشاء مخططات كلاسات ومخططات انسيابية وتصورات معمارية جميلة تجعل الأنظمة المعقدة سهلة الفهم."
              }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 2.2 + index * 0.1, duration: 0.6 }}
                whileHover={{ y: -8, scale: 1.05 }}
                className={`backdrop-blur-sm border rounded-xl p-8 transition-all duration-300 hover:shadow-2xl ${isDarkMode
                  ? 'bg-gray-900/60 border-purple-400/30 hover:bg-gray-900/70 hover:shadow-purple-400/40'
                  : 'bg-white/70 border-gray-200/50 hover:bg-white/90 hover:shadow-gray-400/20'
                  }`}
              >
                <div className="flex flex-col h-full">
                  <div className={`w-16 h-16 rounded-xl flex items-center justify-center mb-6 shadow-lg ${isDarkMode
                    ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white'
                    : 'bg-gradient-to-br from-purple-600 to-pink-600 text-white'
                    }`}>
                    {feature.icon}
                  </div>
                  <h3 className={`text-2xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-black'
                    }`} style={{ textShadow: isDarkMode ? '0 3px 12px rgba(0,0,0,0.9)' : '0 1px 4px rgba(0, 0, 0, 0.97)' }}>
                    {feature.title}
                  </h3>
                  <p className={`leading-relaxed flex-1 ${isDarkMode ? 'text-white' : 'text-black'
                    }`} style={{ textShadow: isDarkMode ? '0 3px 12px rgba(0,0,0,0.9)' : 'none' }}>
                    {feature.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>

      </main>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 3.2, duration: 0.6 }}
        className={`backdrop-blur-sm border-t py-8 ${isDarkMode
          ? 'bg-black/20 border-white/10'
          : 'bg-white/60 border-gray-200/50'
          }`}
      >
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'
            }`} style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0,0,0,0.7)' : 'none' }}>
            Powered by <span className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-800'
              }`}>AutoTest & DocGen</span> • {currentLang === 'EN' ? 'Built for the future of development' : 'مبني لمستقبل التطوير'}
          </p>
        </div>
      </motion.footer>
    </div>
  );
};

export default Home;
