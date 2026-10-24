import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Code2, FileText, GitBranch, Moon, Sun, Globe } from 'lucide-react';
import { i18n } from './utils/i18n';
import './Home.css';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [currentLang, setCurrentLang] = useState<'EN' | 'AR'>('EN');

  useEffect(() => {
    setCurrentLang(i18n.getLanguage() === 'ar' ? 'AR' : 'EN');
  }, []);

  useEffect(() => {
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const handleLanguageChange = () => {
    const newLang = currentLang === 'EN' ? 'AR' : 'EN';
    setCurrentLang(newLang);
    i18n.setLanguage(newLang === 'AR' ? 'ar' : 'en');
  };

  const features = [
    {
      icon: <Code2 size={24} />,
      title: currentLang === 'EN' ? 'AI-Powered Analysis' : 'التحليل بالذكاء الاصطناعي',
      desc: currentLang === 'EN'
        ? 'Deep code understanding with advanced AI algorithms that analyze your codebase for patterns, bugs, and optimization opportunities.'
        : 'فهم عميق للكود باستخدام خوارزميات ذكاء اصطناعي متقدمة تحلل قاعدة الكود للبحث عن الأنماط والأخطاء وفرص التحسين.',
    },
    {
      icon: <FileText size={24} />,
      title: currentLang === 'EN' ? 'Smart Documentation' : 'التوثيق الذكي',
      desc: currentLang === 'EN'
        ? 'Auto-generate comprehensive technical documentation from your codebase with intelligent context-aware descriptions and examples.'
        : 'توليد تلقائي لوثائق تقنية شاملة من قاعدة الكود مع أوصاف وأمثلة ذكية تتناسب مع السياق.',
    },
    {
      icon: <GitBranch size={24} />,
      title: currentLang === 'EN' ? 'Visual Diagrams' : 'المخططات المرئية',
      desc: currentLang === 'EN'
        ? 'Create beautiful class diagrams, flowcharts, and architecture visualizations that make complex systems easy to understand.'
        : 'إنشاء مخططات كلاسات ومخططات انسيابية وتصورات معمارية جميلة تجعل الأنظمة المعقدة سهلة الفهم.',
    },
  ];

  const stats = [
    { value: '500+', label: currentLang === 'EN' ? 'Developers' : 'المطورون' },
    { value: '10k+', label: currentLang === 'EN' ? 'Diagrams Generated' : 'المخططات المولدة' },
    { value: '99.9%', label: currentLang === 'EN' ? 'Uptime' : 'وقت التشغيل' },
  ];

  return (
    <div className={`home-page ${isDarkMode ? 'dark' : 'light'}`}>

      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="home-header"
      >
        <div className="home-logo">
          <div className="home-logo-icon">
            <Code2 size={20} />
          </div>
          <span className="home-logo-text">AutoTest &amp; DocGen</span>
        </div>

        <div className="home-nav-actions">
          <button onClick={handleLanguageChange} className="home-toggle-btn">
            <Globe size={14} />
            {currentLang === 'EN' ? 'EN' : 'عربي'}
          </button>
          <button onClick={() => setIsDarkMode(!isDarkMode)} className="home-toggle-btn">
            {isDarkMode ? <Sun size={14} /> : <Moon size={14} />}
            {isDarkMode
              ? (currentLang === 'EN' ? 'Light' : 'فاتح')
              : (currentLang === 'EN' ? 'Dark' : 'داكن')}
          </button>
        </div>
      </motion.header>

      <main className="home-main">

        {/* Hero */}
        <motion.section
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="home-hero"
        >
          <h1 className="home-hero-title">
            {currentLang === 'EN'
              ? 'Transform Your Code with AI-Powered Analysis'
              : 'حول كودك باستخدام التحليل المعزز بالذكاء الاصطناعي'}
          </h1>
          <p className="home-hero-subtitle">
            {currentLang === 'EN'
              ? 'Cut code review time by 70% with AI-powered analysis, diagrams & docs'
              : 'قلل وقت مراجعة الكود بنسبة 70% باستخدام التحليل المعزز بالذكاء الاصطناعي، المخططات والوثائق'}
          </p>
          <motion.button
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate('/auth')}
            className="home-hero-btn"
          >
            <span>{currentLang === 'EN' ? 'Get Started Now' : 'ابدأ الآن'}</span>
            <ArrowRight size={18} />
          </motion.button>
        </motion.section>

        {/* Stats */}
        <motion.section
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="home-stats"
        >
          {stats.map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 + i * 0.1, duration: 0.5 }}
              className="home-stat-card"
            >
              <div className="home-stat-value">{stat.value}</div>
              <div className="home-stat-label">{stat.label}</div>
            </motion.div>
          ))}
        </motion.section>

        {/* Features */}
        <motion.section
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="home-features"
        >
          {features.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + i * 0.1, duration: 0.5 }}
              className="home-feature-card"
            >
              <div className="home-feature-icon">{feature.icon}</div>
              <h3 className="home-feature-title">{feature.title}</h3>
              <p className="home-feature-desc">{feature.desc}</p>
            </motion.div>
          ))}
        </motion.section>

      </main>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.5 }}
        className="home-footer"
      >
        <p>
          Powered by <span>AutoTest &amp; DocGen</span> &bull;{' '}
          {currentLang === 'EN' ? 'Built for the future of development' : 'مبني لمستقبل التطوير'}
        </p>
      </motion.footer>

    </div>
  );
};

export default Home;
