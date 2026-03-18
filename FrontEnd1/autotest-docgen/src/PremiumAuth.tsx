import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuth } from './context/AuthContext';
import { i18n } from './utils/i18n';
import apiService from './services/api.service';
import './Signup.css';
import {
  Eye,
  EyeOff,
  AlertCircle,
  Sun,
  Moon,
  Globe,
} from 'lucide-react';

import { Button } from './components/ui/Button';
import { Input } from './components/ui/Input';
import { Label } from './components/ui/Label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/Tabs';
import { Checkbox } from './components/ui/Checkbox';

// ────────────────────────────────────────────────
// Form validation schemas
// ────────────────────────────────────────────────
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
  agreeToTerms: z.boolean().refine((val) => val === true, 'You must agree to the terms'),
}).refine((data) => data.password === data.confirmPassword, {
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
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [currentLang, setCurrentLang] = useState<'EN' | 'AR'>('EN');

  const { login } = useAuth();

  // Form hooks
  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      loginIdentifier: '',
      password: '',
      rememberMe: false,
    },
  });

  const signupForm = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      agreeToTerms: false,
    },
  });

  // Initialize i18n & language
  useEffect(() => {
    i18n.init();
    setCurrentLang(i18n.getLanguage() === 'ar' ? 'AR' : 'EN');
  }, []);

  const handleLanguageChange = () => {
    const newLang = currentLang === 'EN' ? 'AR' : 'EN';
    setCurrentLang(newLang);
    i18n.setLanguage(newLang === 'AR' ? 'ar' : 'en');
  };

  // Dark mode
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [isDarkMode]);

  const handleLogin = async (data: LoginFormData) => {
    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      await login({
        username: data.loginIdentifier.trim(),
        password: data.password,
      });
      setSuccess(i18n.t('auth.sign_in_success'));
    } catch (err: unknown) {
      console.error('Login error:', err);
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
      setTimeout(() => {
        setActiveTab('login');
        signupForm.reset();
        setSuccess('');
      }, 2000);
    } catch (err: unknown) {
      console.error('Signup error:', err);
      setError(currentLang === 'EN' ? 'Account creation failed. Please try again.' : 'فشل إنشاء الحساب. حاول مرة أخرى.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`premium-hero ${isDarkMode ? 'dark-mode' : 'light-mode'} ${currentLang === 'AR' ? 'rtl' : 'ltr'}`}>
      {/* Animated Background - يمكنك الاحتفاظ به أو تبسيطه */}
      <div className="animated-bg">
        {/* ... particles و geometric lines ... */}
      </div>

      <div className="relative z-10 min-h-screen flex items-center justify-center p-4 pt-20">
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="w-full max-w-md"
        >
          <div
            className={`backdrop-blur-2xl border rounded-2xl shadow-2xl transition-all duration-500 hover:scale-[1.01] p-8 ${isDarkMode
              ? 'bg-gray-900/60 border-white/20 shadow-purple-300/40 hover:shadow-purple-300/50'
              : 'bg-white/70 border-gray-200/50 shadow-gray-400/20 hover:shadow-gray-400/30'
              } ${currentLang === 'AR' ? 'text-right' : 'text-left'}`}
          >
            {/* Header + toggles */}
            <div className="text-center mb-8">
              {/* Dark/Language toggles */}
              <div className="flex justify-center items-center space-x-3 mb-6">
                <button onClick={() => setIsDarkMode(!isDarkMode)} className={`p-2 rounded-lg border transition-all duration-300 backdrop-blur-sm ${isDarkMode
                  ? 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                  : 'bg-gray-100/50 border-gray-200/50 text-gray-700 hover:bg-gray-200/50'
                  }`}>
                  {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
                </button>
                <button onClick={handleLanguageChange} className={`px-3 py-1.5 rounded-full border text-sm font-medium transition-all duration-300 backdrop-blur-sm ${isDarkMode
                  ? 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                  : 'bg-purple-100/50 border-purple-200/50 text-purple-700 hover:bg-purple-200/50'
                  }`}>
                  <Globe className="h-5 w-5 inline mr-1" />
                  {currentLang}
                </button>
              </div>

              <h1 className={`text-3xl font-bold bg-gradient-to-r bg-clip-text text-transparent drop-shadow-2xl ${isDarkMode
                ? 'from-purple-100 via-pink-100 to-purple-100'
                : 'from-purple-600 via-pink-600 to-purple-600'
                }`}>
                AutoTest & DocGen
              </h1>
              <p className={`text-sm mt-2 ${isDarkMode ? 'text-gray-100' : 'text-gray-600'
                }`} style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0, 0, 0, 0.93)' : 'none' }}>
                {currentLang === 'EN' ? 'Automated testing & documentation' : 'اختبار تلقائي وتوليد وثائق'}
              </p>
            </div>

            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'login' | 'signup')} className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger className={isDarkMode ? 'text-white' : ''} value="login">{currentLang === 'EN' ? 'Sign In' : 'تسجيل الدخول'}</TabsTrigger>
                <TabsTrigger className={isDarkMode ? 'text-white' : ''} value="signup">{currentLang === 'EN' ? 'Sign Up' : 'إنشاء حساب'}</TabsTrigger>
              </TabsList>

              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="w-full"
                >
                  <TabsContent value="login">
                    <form onSubmit={loginForm.handleSubmit(handleLogin)} className="space-y-5">
                      {/* login fields */}
                      <div>
                        <Label className={isDarkMode ? 'text-white' : ''}>{currentLang === 'EN' ? 'Username / Email' : 'اسم المستخدم / البريد الإلكتروني'}</Label>
                        <Input {...loginForm.register('loginIdentifier')} placeholder={currentLang === 'EN' ? 'Enter username or email' : 'أدخل اسم المستخدم أو البريد الإلكتروني'} className={isDarkMode ? 'bg-gray-900/60 border-gray-700 text-white placeholder:text-gray-400' : ''} />
                      </div>
                      <div>
                        <Label className={isDarkMode ? 'text-white' : ''}>{currentLang === 'EN' ? 'Password' : 'كلمة المرور'}</Label>
                        <div className="relative">
                          <Input
                            type={showPassword ? 'text' : 'password'}
                            {...loginForm.register('password')}
                            placeholder={currentLang === 'EN' ? 'Enter password' : 'أدخل كلمة المرور'}
                            className={isDarkMode ? 'bg-gray-900/60 border-gray-700 text-white placeholder:text-gray-400' : ''}
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className={`absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded transition-colors ${isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-700'}`}
                          >
                            {showPassword ? <EyeOff /> : <Eye />}
                          </button>
                        </div>
                      </div>

                      <Button type="submit" className={`w-full font-bold transition-all duration-300 ${isDarkMode
                        ? 'bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white hover:shadow-purple-500/50 hover:brightness-110'
                        : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-purple-400/50 hover:brightness-105'
                        }`} disabled={isLoading}>
                        {isLoading ? (currentLang === 'EN' ? 'Signing in...' : 'جاري الدخول...') : (currentLang === 'EN' ? 'Sign In' : 'تسجيل الدخول')}
                      </Button>
                    </form>
                  </TabsContent>

                  <TabsContent value="signup">
                    <form onSubmit={signupForm.handleSubmit(handleSignup)} className="space-y-5">
                      <div>
                        <Label className={isDarkMode ? 'text-white' : ''}>{currentLang === 'EN' ? 'Username' : 'اسم المستخدم'}</Label>
                        <Input {...signupForm.register('username')} placeholder={currentLang === 'EN' ? 'Enter username' : 'أدخل اسم المستخدم'} className={isDarkMode ? 'bg-gray-900/60 border-gray-700 text-white placeholder:text-gray-400' : ''} />
                        {signupForm.formState.errors.username && (
                          <p className="text-red-400 text-sm mt-1">
                            {signupForm.formState.errors.username.message}
                          </p>
                        )}
                      </div>

                      <div>
                        <Label className={isDarkMode ? 'text-white' : ''}>{currentLang === 'EN' ? 'Email' : 'البريد الإلكتروني'}</Label>
                        <Input {...signupForm.register('email')} placeholder={currentLang === 'EN' ? 'Enter email' : 'أدخل البريد الإلكتروني'} className={isDarkMode ? 'bg-gray-900/60 border-gray-700 text-white placeholder:text-gray-400' : ''} />
                      </div>

                      <div>
                        <Label className={isDarkMode ? 'text-white' : ''}>{currentLang === 'EN' ? 'Password' : 'كلمة المرور'}</Label>
                        <div className="relative">
                          <Input
                            type={showPassword ? 'text' : 'password'}
                            {...signupForm.register('password')}
                            placeholder={currentLang === 'EN' ? 'Enter password' : 'أدخل كلمة المرور'}
                            className={isDarkMode ? 'bg-gray-900/60 border-gray-700 text-white placeholder:text-gray-400' : ''}
                          />
                          <button type="button" onClick={() => setShowPassword(!showPassword)} className={`absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded transition-colors ${isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-500 hover:text-gray-700'}`}>
                            {showPassword ? <EyeOff /> : <Eye />}
                          </button>
                        </div>
                      </div>

                      <div>
                        <Label className={isDarkMode ? 'text-white' : ''}>{currentLang === 'EN' ? 'Confirm Password' : 'تأكيد كلمة المرور'}</Label>
                        <div className="relative">
                          <Input
                            type={showConfirmPassword ? 'text' : 'password'}
                            {...signupForm.register('confirmPassword')}
                            placeholder={currentLang === 'EN' ? 'Confirm password' : 'تأكيد كلمة المرور'}
                            className={isDarkMode ? 'bg-gray-900/60 border-gray-700 text-white placeholder:text-gray-400' : ''}
                          />
                          <button
                            type="button"
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            className={`absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded transition-colors ${isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-500 hover:text-gray-700'}`}
                          >
                            {showConfirmPassword ? <EyeOff /> : <Eye />}
                          </button>
                        </div>
                      </div>

                      {/* ─── التصحيح المهم: Checkbox controlled ─── */}
                      <div className="flex items-center space-x-3">
                        <Checkbox
                          id="agreeToTerms"
                          checked={signupForm.watch('agreeToTerms') ?? false}
                          onCheckedChange={(checked) => {
                            signupForm.setValue('agreeToTerms', !!checked, {
                              shouldValidate: true,
                              shouldDirty: true,
                            });
                          }}
                          className="border-purple-400 data-[state=checked]:bg-purple-600 data-[state=checked]:border-purple-600"
                        />
                        <Label htmlFor="agreeToTerms" className={`text-sm cursor-pointer ${isDarkMode ? 'text-gray-200' : 'text-gray-600'}`} style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0,0,0,0.7)' : 'none' }}>
                          {currentLang === 'EN'
                            ? 'I agree to the Terms of Service and Privacy Policy'
                            : 'أوافق على شروط الخدمة وسياسة الخصوصية'}
                        </Label>
                      </div>

                      {signupForm.formState.errors.agreeToTerms && (
                        <p className={`text-sm flex items-center gap-2 ${isDarkMode ? 'text-red-300' : 'text-red-400'}`}>
                          <AlertCircle size={16} />
                          {signupForm.formState.errors.agreeToTerms.message}
                        </p>
                      )}

                      <Button type="submit" className={`w-full font-bold transition-all duration-300 ${isDarkMode
                        ? 'bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white hover:shadow-purple-500/50 hover:brightness-110'
                        : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-purple-400/50 hover:brightness-105'
                        }`} disabled={isLoading}>
                        {isLoading ? (currentLang === 'EN' ? 'Signing up...' : 'جاري التسجيل...') : (currentLang === 'EN' ? 'Sign Up' : 'إنشاء حساب')}
                      </Button>
                    </form>
                  </TabsContent>
                </motion.div>
              </AnimatePresence>
            </Tabs>

            {/* Success / Error messages */}
            {error && <div className={`mt-4 text-center ${isDarkMode ? 'text-red-200' : 'text-red-500'}`} style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0,0,0,0.7)' : 'none' }}>{error}</div>}
            {success && <div className={`mt-4 text-center ${isDarkMode ? 'text-green-200' : 'text-green-600'}`} style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0,0,0,0.7)' : 'none' }}>{success}</div>}

            {/* Switch tab link */}
            <p className={`text-center mt-6 text-sm ${isDarkMode ? 'text-gray-200' : 'text-gray-600'}`} style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0,0,0,0.7)' : 'none' }}>
              {activeTab === 'login'
                ? (currentLang === 'EN' ? "Don't have an account?" : 'ليس لديك حساب؟')
                : (currentLang === 'EN' ? 'Already have an account?' : 'لديك حساب بالفعل؟')}{' '}
              <button
                type="button"
                onClick={() => setActiveTab(activeTab === 'login' ? 'signup' : 'login')}
                className={`font-medium transition-colors ${isDarkMode ? 'text-purple-200 hover:text-purple-100' : 'text-purple-600 hover:text-purple-700'}`}
                style={{ textShadow: isDarkMode ? '0 2px 8px rgba(0,0,0,0.7)' : 'none' }}
              >
                {activeTab === 'login' ? (currentLang === 'EN' ? 'Sign Up' : 'إنشاء حساب') : (currentLang === 'EN' ? 'Sign In' : 'تسجيل الدخول')}
              </button>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}