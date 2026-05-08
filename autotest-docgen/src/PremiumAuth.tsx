import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuth } from './context/AuthContext';
import { i18n } from './utils/i18n';
import apiService from './services/api.service';
import {
  Eye, EyeOff, AlertCircle, Sun, Moon, Globe,
} from 'lucide-react';
import { Button } from './components/ui/Button';
import { Input } from './components/ui/Input';
import { Label } from './components/ui/Label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/Tabs';
import { Checkbox } from './components/ui/Checkbox';
import './PremiumAuth.css';

const loginSchema = z.object({
  loginIdentifier: z.string().min(1, 'Username or email is required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  rememberMe: z.boolean().optional(),
});

const signupSchema = z.object({
  username: z.string().min(2, 'Username must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string().min(6, 'Please confirm your password'),
  agreeToTerms: z.boolean().refine((v) => v === true, 'You must agree to the terms'),
}).refine((d) => d.password === d.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type LoginFormData = z.infer<typeof loginSchema>;
type SignupFormData = z.infer<typeof signupSchema>;

export default function PremiumAuth() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState<'login' | 'signup'>('login');
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [currentLang, setCurrentLang] = useState<'EN' | 'AR'>('EN');

  const { login } = useAuth();

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { loginIdentifier: '', password: '', rememberMe: false },
  });

  const signupForm = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: { username: '', email: '', password: '', confirmPassword: '', agreeToTerms: false },
  });

  useEffect(() => {
    i18n.init();
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

  const handleLogin = async (data: LoginFormData) => {
    setIsLoading(true);
    setError('');
    try {
      await login({ username: data.loginIdentifier.trim(), password: data.password });
    } catch {
      setError(currentLang === 'EN' ? 'Login failed. Please check your credentials.' : 'فشل تسجيل الدخول. تحقق من بياناتك.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (data: SignupFormData) => {
    setIsLoading(true);
    setError('');
    setSuccess('');
    try {
      await apiService.auth.signup({
        username: data.username.trim().replace(/\s+/g, '').toLowerCase(),
        password: data.password,
        email: data.email.trim(),
      });
      setSuccess(i18n.t('auth.sign_up_success'));
      setTimeout(() => { setActiveTab('login'); signupForm.reset(); setSuccess(''); }, 2000);
    } catch {
      setError(currentLang === 'EN' ? 'Account creation failed. Please try again.' : 'فشل إنشاء الحساب. حاول مرة أخرى.');
    } finally {
      setIsLoading(false);
    }
  };

  const dark = isDarkMode;

  // Shared input classes
  const inputCls = dark
    ? 'bg-gray-900/60 border-gray-700 text-white placeholder:text-gray-400 focus-visible:ring-purple-500'
    : 'bg-white border-gray-200 text-gray-900 placeholder:text-gray-400 focus-visible:ring-purple-400';

  const labelCls = dark ? 'text-gray-200' : 'text-gray-700';

  return (
    <div
      className="auth-page-wrap"
      style={{
        background: dark
          ? 'linear-gradient(135deg, #0f0a1e 0%, #1a1035 50%, #0f172a 100%)'
          : 'linear-gradient(135deg, #f8fafc 0%, #eef2ff 50%, #fce7f3 100%)',
      }}
      dir={currentLang === 'AR' ? 'rtl' : 'ltr'}
    >
      {/* Animated background layers */}
      <div className="auth-mesh" aria-hidden="true" />
      <div className="auth-glow-tr" aria-hidden="true" />
      <div className="auth-glow-bl" aria-hidden="true" />
      <div className="auth-glow-center" aria-hidden="true" />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: 'easeOut' }}
        className="auth-card-wrap"
      >
        <div
          className="rounded-2xl p-8 relative"
          style={{
            background: dark ? 'rgba(26, 16, 53, 0.97)' : 'rgba(255, 255, 255, 0.97)',
            border: `1px solid ${dark ? 'rgba(118,75,162,0.30)' : 'rgba(118,75,162,0.18)'}`,
            boxShadow: dark
              ? '0 8px 40px rgba(240,147,251,0.15)'
              : '0 8px 40px rgba(118,75,162,0.15)',
            backdropFilter: 'blur(20px)',
          }}
        >
          {/* Controls */}
          <div className="absolute top-4 right-4 flex items-center gap-2">
            <button
              onClick={handleLanguageChange}
              className="flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium border transition-all"
              style={{
                background: dark ? 'rgba(118,75,162,0.20)' : 'rgba(118,75,162,0.08)',
                borderColor: dark ? 'rgba(118,75,162,0.35)' : 'rgba(118,75,162,0.20)',
                color: dark ? '#e9d5ff' : '#764ba2',
              }}
            >
              <Globe size={12} />
              {currentLang}
            </button>
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-1.5 rounded-lg border transition-all"
              style={{
                background: dark ? 'rgba(118,75,162,0.20)' : 'rgba(118,75,162,0.08)',
                borderColor: dark ? 'rgba(118,75,162,0.35)' : 'rgba(118,75,162,0.20)',
                color: dark ? '#e9d5ff' : '#764ba2',
              }}
            >
              {dark ? <Sun size={14} /> : <Moon size={14} />}
            </button>
          </div>

          {/* Title */}
          <div className="text-center mb-8 mt-2">
            <h1
              className="text-2xl font-extrabold mb-1"
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              AutoTest &amp; DocGen
            </h1>
            <p className="text-sm" style={{ color: dark ? '#a78bca' : '#64748b' }}>
              {currentLang === 'EN' ? 'Automated testing & documentation' : 'اختبار تلقائي وتوليد وثائق'}
            </p>
          </div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'login' | 'signup')} className="w-full">
            <TabsList
              className="grid w-full grid-cols-2 mb-6"
              style={{
                background: dark ? 'rgba(40,22,75,0.80)' : 'rgba(248,250,252,0.9)',
                border: `1px solid ${dark ? 'rgba(118,75,162,0.30)' : 'rgba(118,75,162,0.18)'}`,
              }}
            >
              <TabsTrigger
                value="login"
                className="auth-tab-trigger"
                data-active={activeTab === 'login' ? 'true' : 'false'}
                data-dark={dark ? 'true' : 'false'}
                style={activeTab === 'login'
                  ? { background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#ffffff', border: 'none' }
                  : { color: dark ? '#e9d5ff' : '#764ba2', background: 'transparent' }
                }
              >
                {currentLang === 'EN' ? 'Sign In' : 'تسجيل الدخول'}
              </TabsTrigger>
              <TabsTrigger
                value="signup"
                className="auth-tab-trigger"
                data-active={activeTab === 'signup' ? 'true' : 'false'}
                data-dark={dark ? 'true' : 'false'}
                style={activeTab === 'signup'
                  ? { background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#ffffff', border: 'none' }
                  : { color: dark ? '#e9d5ff' : '#764ba2', background: 'transparent' }
                }
              >
                {currentLang === 'EN' ? 'Sign Up' : 'إنشاء حساب'}
              </TabsTrigger>
            </TabsList>

            {/* Error / Success */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="mb-4 p-3 rounded-lg flex items-center gap-2 text-sm"
                  style={{
                    background: dark ? 'rgba(220,38,38,0.12)' : 'rgba(220,38,38,0.08)',
                    border: '1px solid rgba(220,38,38,0.25)',
                    color: dark ? '#fca5a5' : '#dc2626',
                  }}
                >
                  <AlertCircle size={14} />{error}
                </motion.div>
              )}
              {success && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="mb-4 p-3 rounded-lg flex items-center gap-2 text-sm"
                  style={{
                    background: dark ? 'rgba(16,185,129,0.12)' : 'rgba(16,185,129,0.08)',
                    border: '1px solid rgba(16,185,129,0.25)',
                    color: dark ? '#6ee7b7' : '#059669',
                  }}
                >
                  {success}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Login */}
            <TabsContent value="login">
              <form onSubmit={loginForm.handleSubmit(handleLogin)} className="space-y-4">
                <div className="space-y-1.5">
                  <Label className={labelCls}>
                    {currentLang === 'EN' ? 'Username / Email' : 'اسم المستخدم / البريد'}
                  </Label>
                  <Input
                    {...loginForm.register('loginIdentifier')}
                    placeholder={currentLang === 'EN' ? 'Enter username or email' : 'أدخل اسم المستخدم أو البريد'}
                    className={inputCls}
                    disabled={isLoading}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className={labelCls}>
                    {currentLang === 'EN' ? 'Password' : 'كلمة المرور'}
                  </Label>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      {...loginForm.register('password')}
                      placeholder={currentLang === 'EN' ? 'Enter password' : 'أدخل كلمة المرور'}
                      className={inputCls}
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2"
                      style={{ color: dark ? '#6b7280' : '#94a3b8' }}
                    >
                      {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: dark ? '#a78bca' : '#64748b' }}>
                    <input type="checkbox" {...loginForm.register('rememberMe')} className="accent-purple-600" />
                    {currentLang === 'EN' ? 'Remember me' : 'تذكرني'}
                  </label>
                  <button type="button" className="text-sm" style={{ color: dark ? '#a78bca' : '#764ba2' }}>
                    {currentLang === 'EN' ? 'Forgot password?' : 'نسيت كلمة المرور؟'}
                  </button>
                </div>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full font-semibold"
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    border: 'none',
                  }}
                >
                  {isLoading
                    ? (currentLang === 'EN' ? 'Signing in...' : 'جاري الدخول...')
                    : (currentLang === 'EN' ? 'Sign In' : 'تسجيل الدخول')}
                </Button>
              </form>
            </TabsContent>

            {/* Signup */}
            <TabsContent value="signup">
              <form onSubmit={signupForm.handleSubmit(handleSignup)} className="space-y-4">
                <div className="space-y-1.5">
                  <Label className={labelCls}>{currentLang === 'EN' ? 'Username' : 'اسم المستخدم'}</Label>
                  <Input {...signupForm.register('username')} placeholder={currentLang === 'EN' ? 'Enter username' : 'أدخل اسم المستخدم'} className={inputCls} disabled={isLoading} />
                  {signupForm.formState.errors.username && <p className="text-xs text-red-400">{signupForm.formState.errors.username.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label className={labelCls}>{currentLang === 'EN' ? 'Email' : 'البريد الإلكتروني'}</Label>
                  <Input {...signupForm.register('email')} type="email" placeholder={currentLang === 'EN' ? 'Enter email' : 'أدخل البريد'} className={inputCls} disabled={isLoading} />
                  {signupForm.formState.errors.email && <p className="text-xs text-red-400">{signupForm.formState.errors.email.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label className={labelCls}>{currentLang === 'EN' ? 'Password' : 'كلمة المرور'}</Label>
                  <div className="relative">
                    <Input type={showPassword ? 'text' : 'password'} {...signupForm.register('password')} placeholder={currentLang === 'EN' ? 'Create a password' : 'أنشئ كلمة مرور'} className={inputCls} disabled={isLoading} />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: dark ? '#6b7280' : '#94a3b8' }}>
                      {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                  {signupForm.formState.errors.password && <p className="text-xs text-red-400">{signupForm.formState.errors.password.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label className={labelCls}>{currentLang === 'EN' ? 'Confirm Password' : 'تأكيد كلمة المرور'}</Label>
                  <div className="relative">
                    <Input type={showConfirmPassword ? 'text' : 'password'} {...signupForm.register('confirmPassword')} placeholder={currentLang === 'EN' ? 'Confirm password' : 'تأكيد كلمة المرور'} className={inputCls} disabled={isLoading} />
                    <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: dark ? '#6b7280' : '#94a3b8' }}>
                      {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                  {signupForm.formState.errors.confirmPassword && <p className="text-xs text-red-400">{signupForm.formState.errors.confirmPassword.message}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="agreeToTerms"
                    checked={signupForm.watch('agreeToTerms') ?? false}
                    onCheckedChange={(c) => signupForm.setValue('agreeToTerms', !!c, { shouldValidate: true })}
                    className="border-purple-400 data-[state=checked]:bg-purple-600"
                  />
                  <Label htmlFor="agreeToTerms" className={`text-sm cursor-pointer ${labelCls}`}>
                    {currentLang === 'EN' ? 'I agree to the Terms of Service and Privacy Policy' : 'أوافق على شروط الخدمة وسياسة الخصوصية'}
                  </Label>
                </div>
                {signupForm.formState.errors.agreeToTerms && <p className="text-xs text-red-400">{signupForm.formState.errors.agreeToTerms.message}</p>}
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full font-semibold"
                  style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none' }}
                >
                  {isLoading
                    ? (currentLang === 'EN' ? 'Creating account...' : 'جاري التسجيل...')
                    : (currentLang === 'EN' ? 'Sign Up' : 'إنشاء حساب')}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          {/* Footer */}
          <p className="text-center mt-6 text-sm" style={{ color: dark ? '#a78bca' : '#64748b' }}>
            {activeTab === 'login'
              ? (currentLang === 'EN' ? "Don't have an account? " : 'ليس لديك حساب؟ ')
              : (currentLang === 'EN' ? 'Already have an account? ' : 'لديك حساب بالفعل؟ ')}
            <button
              type="button"
              onClick={() => setActiveTab(activeTab === 'login' ? 'signup' : 'login')}
              className="font-semibold underline"
              style={{ color: dark ? '#c084fc' : '#764ba2' }}
            >
              {activeTab === 'login'
                ? (currentLang === 'EN' ? 'Sign Up' : 'إنشاء حساب')
                : (currentLang === 'EN' ? 'Sign In' : 'تسجيل الدخول')}
            </button>
          </p>
          <p className="text-center mt-2 text-xs" style={{ color: dark ? '#6b7280' : '#94a3b8' }}>
            Powered by{' '}
            <span style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontWeight: 600 }}>
              AutoTest &amp; DocGen
            </span>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
