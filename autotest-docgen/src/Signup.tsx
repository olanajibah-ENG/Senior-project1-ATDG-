import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from './context/AuthContext';
import { i18n } from './utils/i18n';
import apiService from './services/api.service';
import {
  Eye, EyeOff, Check, AlertCircle, LogIn, UserPlus,
  Mail, User, Lock, Loader2, Github, Chrome, Code2, Moon, Sun, Globe
} from 'lucide-react';
import './Signup.css';

const loginSchema = z.object({
  loginIdentifier: z.string().min(1, 'Email or username is required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  rememberMe: z.boolean().optional(),
});

const signupSchema = z.object({
  fullName: z.string().min(2, 'Full name must be at least 2 characters'),
  signUpEmail: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  agreeToTerms: z.boolean().refine(val => val === true, 'You must agree to the terms'),
});

type LoginFormData = z.infer<typeof loginSchema>;
type SignupFormData = z.infer<typeof signupSchema>;

export default function SignUp() {
  const [activeTab, setActiveTab] = useState<'login' | 'signup'>('login');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [currentLang, setCurrentLang] = useState<'EN' | 'AR'>('EN');

  const { login } = useAuth();

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

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { loginIdentifier: '', password: '', rememberMe: false },
  });

  const signupForm = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: { fullName: '', signUpEmail: '', password: '', agreeToTerms: false },
  });

  const onLoginSubmit = async (data: LoginFormData) => {
    try {
      setIsLoading(true);
      setError('');
      setSuccess('');
      await login({ username: data.loginIdentifier.trim(), password: data.password });
      setSuccess(i18n.t('auth.sign_in_success'));
    } catch (err: unknown) {
      let msg = 'Authentication failed. Please check your details.';
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const e = err as { response?: { data?: { detail?: string } } };
        if (e.response?.data?.detail) msg = e.response.data.detail;
      }
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const onSignupSubmit = async (data: SignupFormData) => {
    try {
      setIsLoading(true);
      setError('');
      setSuccess('');
      await apiService.auth.signup({
        username: data.fullName.trim().replace(/\s+/g, '').toLowerCase(),
        password: data.password,
        email: data.signUpEmail.trim(),
      });
      setSuccess(i18n.t('auth.sign_up_success'));
      setTimeout(() => { setActiveTab('login'); signupForm.reset(); }, 2000);
    } catch (err: unknown) {
      let msg = 'Signup failed. Please try again.';
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const e = err as { response?: { data?: { detail?: string } } };
        if (e.response?.data?.detail) msg = e.response.data.detail;
      }
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`auth-page ${isDarkMode ? 'dark' : 'light'}`}>
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: 'easeOut' }}
        className="auth-card"
      >
        {/* Controls */}
        <div className="auth-controls">
          <button
            onClick={handleLanguageChange}
            className="auth-social-btn"
            style={{ padding: '5px 10px', fontSize: '0.75rem' }}
          >
            <Globe size={13} />
            {currentLang === 'EN' ? 'EN' : 'عربي'}
          </button>
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="auth-social-btn"
            style={{ padding: '5px 9px' }}
          >
            {isDarkMode ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>

        {/* Header */}
        <div className="auth-header">
          <div className="auth-logo">
            <Code2 size={24} />
          </div>
          <h1 className="auth-title">Welcome to AutoTest &amp; DocGen</h1>
          <p className="auth-subtitle">Automated testing and documentation generation for your projects</p>
        </div>

        {/* Tabs */}
        <div className="auth-tabs">
          <button
            className={`auth-tab ${activeTab === 'login' ? 'active' : ''}`}
            onClick={() => setActiveTab('login')}
          >
            <LogIn size={15} />
            Sign In
          </button>
          <button
            className={`auth-tab ${activeTab === 'signup' ? 'active' : ''}`}
            onClick={() => setActiveTab('signup')}
          >
            <UserPlus size={15} />
            Sign Up
          </button>
        </div>

        {/* Messages */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="auth-error"
            >
              <AlertCircle size={15} />
              {error}
            </motion.div>
          )}
          {success && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="auth-success"
            >
              <Check size={15} />
              {success}
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Login Form ── */}
        {activeTab === 'login' && (
          <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="auth-form">

            <div className="auth-form-group">
              <label htmlFor="loginIdentifier" className="auth-label">Email or Username</label>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon"><User size={15} /></span>
                <input
                  id="loginIdentifier"
                  {...loginForm.register('loginIdentifier')}
                  type="text"
                  placeholder="Enter your email or username"
                  className="auth-input"
                  disabled={isLoading}
                />
              </div>
              {loginForm.formState.errors.loginIdentifier && (
                <span className="auth-field-error">
                  <AlertCircle size={12} />
                  {loginForm.formState.errors.loginIdentifier.message}
                </span>
              )}
            </div>

            <div className="auth-form-group">
              <label htmlFor="loginPassword" className="auth-label">Password</label>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon"><Lock size={15} /></span>
                <input
                  id="loginPassword"
                  {...loginForm.register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  className="auth-input"
                  style={{ paddingRight: '40px' }}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="auth-input-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {loginForm.formState.errors.password && (
                <span className="auth-field-error">
                  <AlertCircle size={12} />
                  {loginForm.formState.errors.password.message}
                </span>
              )}
            </div>

            <div className="auth-row">
              <label className="auth-row-label">
                <input type="checkbox" {...loginForm.register('rememberMe')} disabled={isLoading} />
                Remember me
              </label>
              <button type="button" className="auth-link-btn">Forgot password?</button>
            </div>

            <button type="submit" disabled={isLoading} className="auth-submit">
              {isLoading
                ? <><Loader2 size={16} className="animate-spin" /> Signing in...</>
                : <><LogIn size={16} /> Sign In</>}
            </button>
          </form>
        )}

        {/* ── Signup Form ── */}
        {activeTab === 'signup' && (
          <form onSubmit={signupForm.handleSubmit(onSignupSubmit)} className="auth-form">

            <div className="auth-form-group">
              <label htmlFor="fullName" className="auth-label">Full Name</label>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon"><User size={15} /></span>
                <input
                  id="fullName"
                  {...signupForm.register('fullName')}
                  type="text"
                  placeholder="Enter your full name"
                  className="auth-input"
                  disabled={isLoading}
                />
              </div>
              {signupForm.formState.errors.fullName && (
                <span className="auth-field-error">
                  <AlertCircle size={12} />
                  {signupForm.formState.errors.fullName.message}
                </span>
              )}
            </div>

            <div className="auth-form-group">
              <label htmlFor="signUpEmail" className="auth-label">Email</label>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon"><Mail size={15} /></span>
                <input
                  id="signUpEmail"
                  {...signupForm.register('signUpEmail')}
                  type="email"
                  placeholder="Enter your email"
                  className="auth-input"
                  disabled={isLoading}
                />
              </div>
              {signupForm.formState.errors.signUpEmail && (
                <span className="auth-field-error">
                  <AlertCircle size={12} />
                  {signupForm.formState.errors.signUpEmail.message}
                </span>
              )}
            </div>

            <div className="auth-form-group">
              <label htmlFor="signupPassword" className="auth-label">Password</label>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon"><Lock size={15} /></span>
                <input
                  id="signupPassword"
                  {...signupForm.register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Create a password"
                  className="auth-input"
                  style={{ paddingRight: '40px' }}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="auth-input-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {signupForm.formState.errors.password && (
                <span className="auth-field-error">
                  <AlertCircle size={12} />
                  {signupForm.formState.errors.password.message}
                </span>
              )}
            </div>

            <label className="auth-checkbox-wrap">
              <input
                type="checkbox"
                {...signupForm.register('agreeToTerms')}
                disabled={isLoading}
              />
              I agree to the Terms of Service and Privacy Policy
            </label>
            {signupForm.formState.errors.agreeToTerms && (
              <span className="auth-field-error">
                <AlertCircle size={12} />
                {signupForm.formState.errors.agreeToTerms.message}
              </span>
            )}

            <button type="submit" disabled={isLoading} className="auth-submit">
              {isLoading
                ? <><Loader2 size={16} className="animate-spin" /> Creating account...</>
                : <><UserPlus size={16} /> Sign Up</>}
            </button>
          </form>
        )}

        {/* Social */}
        <div className="auth-divider">
          <div className="auth-divider-line" />
          <span className="auth-divider-text">Or continue with</span>
          <div className="auth-divider-line" />
        </div>

        <div className="auth-social">
          <button className="auth-social-btn" disabled={isLoading}>
            <Chrome size={15} /> Google
          </button>
          <button className="auth-social-btn" disabled={isLoading}>
            <Github size={15} /> GitHub
          </button>
        </div>

        {/* Footer */}
        <div className="auth-footer">
          <p className="auth-footer-text">
            {activeTab === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button
              type="button"
              className="auth-link-btn"
              onClick={() => setActiveTab(activeTab === 'login' ? 'signup' : 'login')}
            >
              {activeTab === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>
          <p className="auth-footer-powered">
            Powered by <span>AutoTest &amp; DocGen</span>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
