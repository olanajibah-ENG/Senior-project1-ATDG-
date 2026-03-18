import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from './context/AuthContext';
import { i18n } from './utils/i18n';
import apiService from './services/api.service';
import { Eye, EyeOff, Check, AlertCircle, LogIn, UserPlus, Mail, User, Lock, Loader2, Github, Chrome } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/Tabs';
import { Button } from './components/ui/Button';
import { Input } from './components/ui/Input';
import { Label } from './components/ui/Label';
import { ModeToggle } from './components/mode-toggle';
import { LanguageSelector } from './components/language-selector';
import './Signup.css';

// Zod schemas for validation
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

  const { login } = useAuth();

  // React Hook Form instances
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
      fullName: '',
      signUpEmail: '',
      password: '',
      agreeToTerms: false,
    },
  });

  const onLoginSubmit = async (data: LoginFormData) => {
    try {
      setIsLoading(true);
      setError('');
      setSuccess('');

      await login({
        username: data.loginIdentifier.trim(),
        password: data.password
      });
      setSuccess(i18n.t('auth.sign_in_success'));
    } catch (err: unknown) {
      console.error('Authentication error:', err);
      let errorMessage = 'Authentication failed. Please check your details.';

      if (typeof err === 'object' && err !== null && 'response' in err) {
        const errObj = err as {
          response?: {
            status?: number;
            data?: {
              detail?: string;
              [key: string]: any;
            };
            statusText?: string;
          };
          message?: string;
        };

        if (errObj.response?.data?.detail) {
          errorMessage = errObj.response.data.detail;
        }
      }

      setError(errorMessage);
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
        email: data.signUpEmail.trim()
      });
      setSuccess(i18n.t('auth.sign_up_success'));
      setTimeout(() => {
        setActiveTab('login');
        signupForm.reset();
      }, 2000);
    } catch (err: unknown) {
      console.error('Signup error:', err);
      let errorMessage = 'Signup failed. Please try again.';

      if (typeof err === 'object' && err !== null && 'response' in err) {
        const errObj = err as {
          response?: {
            status?: number;
            data?: {
              detail?: string;
              [key: string]: any;
            };
            statusText?: string;
          };
          message?: string;
        };

        if (errObj.response?.data?.detail) {
          errorMessage = errObj.response.data.detail;
        }
      }

      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-950 via-purple-950 to-pink-950 animate-gradient-slow" />
      <div className="absolute inset-0 bg-gradient-to-tr from-blue-950 via-violet-950 to-indigo-950 opacity-50 animate-gradient-slow animation-delay-2000" />

      {/* Subtle noise texture overlay */}
      <div className="absolute inset-0 opacity-20 mix-blend-overlay">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJhIiB4PSIwIiB5PSIwIj48ZmVUdXJidWxlbmNlIGJhc2VGcmVxdWVuY3k9Ii43NSIgc3RpdGNoVGlsZXM9InN0aXRjaCIgdHlwZT0iZnJhY3RhbE5vaXNlIi8+PGZlQ29sb3JNYXRyaXggdHlwZT0ic2F0dXJhdGUiIHZhbHVlcz0iMCIvPjwvZmlsdGVyPjxwYXRoIGQ9Ik0wIDBoMzAwdjMwMEgweiIgZmlsdGVyPSJ1cmwoI2EpIiBvcGFjaXR5PSIuMDUiLz48L3N2Zz4=')] bg-repeat" />
      </div>

      {/* Main glassmorphism card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="relative w-full max-w-md"
      >
        <div className="backdrop-blur-3xl bg-white/10 dark:bg-black/40 border border-white/20 dark:border-white/10 rounded-3xl shadow-2xl shadow-purple-500/20 hover:shadow-purple-500/30 transition-all duration-300 p-8 hover:scale-105">
          {/* Theme Toggle and Language Selector */}
          <ModeToggle />
          <LanguageSelector />

          {/* Header */}
          <div className="text-center mb-8">
            <motion.h1
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1, duration: 0.3 }}
              className="text-3xl font-bold text-white dark:text-gray-100 mb-2"
            >
              Welcome to AutoTest & DocGen
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.3 }}
              className="text-white/70 dark:text-gray-300 text-sm"
            >
              Automated testing and documentation generation for your projects
            </motion.p>
          </div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'login' | 'signup')} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6 bg-white/10 dark:bg-black/20 border border-white/10 dark:border-white/5">
              <TabsTrigger
                value="login"
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-violet-600/20 data-[state=active]:to-indigo-600/20 data-[state=active]:text-white dark:data-[state=active]:text-gray-100 text-white/70 dark:text-gray-300 transition-all duration-200 relative data-[state=active]:after:absolute data-[state=active]:after:bottom-0 data-[state=active]:after:left-0 data-[state=active]:after:w-full data-[state=active]:after:h-0.5 data-[state=active]:after:bg-gradient-to-r data-[state=active]:after:from-violet-600 data-[state=active]:after:to-indigo-600"
              >
                <LogIn className="w-4 h-4 mr-2" />
                Sign In
              </TabsTrigger>
              <TabsTrigger
                value="signup"
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-violet-600/20 data-[state=active]:to-indigo-600/20 data-[state=active]:text-white dark:data-[state=active]:text-gray-100 text-white/70 dark:text-gray-300 transition-all duration-200 relative data-[state=active]:after:absolute data-[state=active]:after:bottom-0 data-[state=active]:after:left-0 data-[state=active]:after:w-full data-[state=active]:after:h-0.5 data-[state=active]:after:bg-gradient-to-r data-[state=active]:after:from-violet-600 data-[state=active]:after:to-indigo-600"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Sign Up
              </TabsTrigger>
            </TabsList>

            {/* Error/Success messages */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10, x: 0 }}
                  animate={{ opacity: 1, y: 0, x: [0, -5, 5, -5, 5, 0] }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-200 text-sm flex items-center"
                >
                  <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                  {error}
                </motion.div>
              )}

              {success && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="mb-4 p-3 bg-green-500/20 border border-green-500/30 rounded-lg text-green-200 text-sm flex items-center"
                >
                  <Check className="w-4 h-4 mr-2 flex-shrink-0" />
                  {success}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Login Form */}
            <TabsContent value="login" className="space-y-4">
              <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="loginIdentifier" className="text-white/80 dark:text-gray-200 text-sm font-medium">
                    Email or Username
                  </Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 w-4 h-4" />
                    <Input
                      id="loginIdentifier"
                      {...loginForm.register('loginIdentifier')}
                      type="text"
                      placeholder="Enter your email or username"
                      className="pl-10 bg-white/10 border-white/20 text-white placeholder-white/50 focus:border-purple-400 focus:ring-purple-400/20"
                      disabled={isLoading}
                    />
                  </div>
                  {loginForm.formState.errors.loginIdentifier && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-red-300 text-xs flex items-center"
                    >
                      <AlertCircle className="w-3 h-3 mr-1" />
                      {loginForm.formState.errors.loginIdentifier.message}
                    </motion.p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="loginPassword" className="text-white/80 dark:text-gray-200 text-sm font-medium">
                    Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 w-4 h-4" />
                    <Input
                      id="loginPassword"
                      {...loginForm.register('password')}
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your password"
                      className="pl-10 pr-10 bg-white/10 border-white/20 text-white placeholder-white/50 focus:border-purple-400 focus:ring-purple-400/20"
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50 hover:text-white/70 transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {loginForm.formState.errors.password && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-red-300 text-xs flex items-center"
                    >
                      <AlertCircle className="w-3 h-3 mr-1" />
                      {loginForm.formState.errors.password.message}
                    </motion.p>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <input
                      id="rememberMe"
                      {...loginForm.register('rememberMe')}
                      type="checkbox"
                      className="rounded border-white/20 dark:border-white/10 bg-white/10 dark:bg-black/20 text-purple-500 focus:ring-purple-400/20"
                      disabled={isLoading}
                    />
                    <Label htmlFor="rememberMe" className="text-white/70 dark:text-gray-300 text-sm">
                      Remember me
                    </Label>
                  </div>
                  <button
                    type="button"
                    className="text-purple-300 hover:text-purple-200 dark:text-purple-400 dark:hover:text-purple-300 text-sm transition-colors"
                  >
                    Forgot password?
                  </button>
                </div>

                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white font-medium py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-purple-500/25"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Signing in...
                      </>
                    ) : (
                      <>
                        <LogIn className="w-4 h-4 mr-2" />
                        Sign In
                      </>
                    )}
                  </Button>
                </motion.div>
              </form>
            </TabsContent>

            {/* Signup Form */}
            <TabsContent value="signup" className="space-y-4">
              <form onSubmit={signupForm.handleSubmit(onSignupSubmit)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="fullName" className="text-white/80 dark:text-gray-200 text-sm font-medium">
                    Full Name
                  </Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 w-4 h-4" />
                    <Input
                      id="fullName"
                      {...signupForm.register('fullName')}
                      type="text"
                      placeholder="Enter your full name"
                      className="pl-10 bg-white/10 border-white/20 text-white placeholder-white/50 focus:border-purple-400 focus:ring-purple-400/20"
                      disabled={isLoading}
                    />
                  </div>
                  {signupForm.formState.errors.fullName && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-red-300 text-xs flex items-center"
                    >
                      <AlertCircle className="w-3 h-3 mr-1" />
                      {signupForm.formState.errors.fullName.message}
                    </motion.p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="signUpEmail" className="text-white/80 text-sm font-medium">
                    Email
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 w-4 h-4" />
                    <Input
                      id="signUpEmail"
                      {...signupForm.register('signUpEmail')}
                      type="email"
                      placeholder="Enter your email"
                      className="pl-10 bg-white/10 border-white/20 text-white placeholder-white/50 focus:border-purple-400 focus:ring-purple-400/20"
                      disabled={isLoading}
                    />
                  </div>
                  {signupForm.formState.errors.signUpEmail && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-red-300 text-xs flex items-center"
                    >
                      <AlertCircle className="w-3 h-3 mr-1" />
                      {signupForm.formState.errors.signUpEmail.message}
                    </motion.p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="signupPassword" className="text-white/80 text-sm font-medium">
                    Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 w-4 h-4" />
                    <Input
                      id="signupPassword"
                      {...signupForm.register('password')}
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Create a password"
                      className="pl-10 pr-10 bg-white/10 border-white/20 text-white placeholder-white/50 focus:border-purple-400 focus:ring-purple-400/20"
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50 hover:text-white/70 transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {signupForm.formState.errors.password && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-red-300 text-xs flex items-center"
                    >
                      <AlertCircle className="w-3 h-3 mr-1" />
                      {signupForm.formState.errors.password.message}
                    </motion.p>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    id="agreeToTerms"
                    {...signupForm.register('agreeToTerms')}
                    type="checkbox"
                    className="rounded border-white/20 bg-white/10 text-purple-500 focus:ring-purple-400/20"
                    disabled={isLoading}
                  />
                  <Label htmlFor="agreeToTerms" className="text-white/70 text-sm">
                    I agree to the Terms of Service and Privacy Policy
                  </Label>
                </div>
                {signupForm.formState.errors.agreeToTerms && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-300 text-xs flex items-center"
                  >
                    <AlertCircle className="w-3 h-3 mr-1" />
                    {signupForm.formState.errors.agreeToTerms.message}
                  </motion.p>
                )}

                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white font-medium py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-purple-500/25"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Creating account...
                      </>
                    ) : (
                      <>
                        <UserPlus className="w-4 h-4 mr-2" />
                        Sign Up
                      </>
                    )}
                  </Button>
                </motion.div>
              </form>
            </TabsContent>
          </Tabs>

          {/* Social auth divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-transparent px-2 text-white/50">Or continue with</span>
            </div>
          </div>

          {/* Social buttons */}
          <div className="grid grid-cols-2 gap-3">
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                variant="outline"
                className="w-full bg-white/10 dark:bg-black/20 border-white/20 dark:border-white/10 text-white dark:text-gray-100 hover:bg-white/20 dark:hover:bg-black/30 transition-all duration-200"
                disabled={isLoading}
              >
                <Chrome className="w-3 h-3 mr-2" />
                Google
              </Button>
            </motion.div>
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                variant="outline"
                className="w-full bg-white/10 dark:bg-black/20 border-white/20 dark:border-white/10 text-white dark:text-gray-100 hover:bg-white/20 dark:hover:bg-black/30 transition-all duration-200"
                disabled={isLoading}
              >
                <Github className="w-3 h-3 mr-2" />
                GitHub
              </Button>
            </motion.div>
          </div>

          {/* Footer */}
          <div className="mt-6 text-center">
            <p className="text-white/60 text-xs">
              {activeTab === 'login' ? "Don't have an account? " : "Already have an account? "}
              <button
                type="button"
                onClick={() => setActiveTab(activeTab === 'login' ? 'signup' : 'login')}
                className="text-purple-300 hover:text-purple-200 underline transition-colors"
              >
                {activeTab === 'login' ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>

          {/* Powered by */}
          <div className="mt-4 text-center">
            <p className="text-white/40 text-xs">
              Powered by{' '}
              <span className="bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent font-medium">
                AutoTest & DocGen
              </span>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}