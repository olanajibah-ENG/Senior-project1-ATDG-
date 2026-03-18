import React, { createContext, useState, useContext, type ReactNode, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService, { type LoginData, type AuthResponse, type CurrentUser } from '../services/api.service';

// ----------------------------------------------------
// تحديد الأنواع (Types)
// ----------------------------------------------------

// نوع بيانات الـ Context
interface AuthContextType {
  user: CurrentUser | null;
  isLoggedIn: boolean;
  // دالة login أصبحت async وتستقبل بيانات الدخول
  login: (credentials: LoginData) => Promise<void>; 
  logout: () => void;
}

// القيمة الافتراضية للـ Context
const defaultAuthContext: AuthContextType = {
  user: null,
  isLoggedIn: false,
  login: () => Promise.resolve(), // يجب أن تكون دالة async افتراضية
  logout: () => {},
};

export const AuthContext = createContext<AuthContextType>(defaultAuthContext);

interface AuthProviderProps {
  children: ReactNode;
}

// ----------------------------------------------------
// مكون الموفر (AuthProvider)
// ----------------------------------------------------
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const navigate = useNavigate(); // لاستخدام التوجيه (Redirection)
  const [user, setUser] = useState<CurrentUser | null>(null);

  // دالة تحميل بيانات المستخدم من localStorage
  const loadUserFromStorage = () => {
    try {
      const storedUser = localStorage.getItem('user');
      const accessToken = localStorage.getItem('access_token');
      
      if (storedUser && accessToken) {
        const userData: CurrentUser = JSON.parse(storedUser);
        setUser(userData);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Error loading user from storage:', error);
      setUser(null);
    }
  };

  // دالة تسجيل الخروج
  const logout = useCallback(() => {
    // حذف التوكنات وإعادة تعيين المستخدم
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    navigate('/signup');
  }, [navigate]);

  // قراءة المستخدم عند تحميل التطبيق لأول مرة
  useEffect(() => {
    loadUserFromStorage();

    // Listen for logout events from apiClient interceptor
    const handleLogoutEvent = () => {
      logout();
    };

    window.addEventListener('auth:logout', handleLogoutEvent);

    return () => {
      window.removeEventListener('auth:logout', handleLogoutEvent);
    };
  }, [logout]);

  // دالة تسجيل الدخول الفعلي (تُستدعى من Signup/Login)
  const login = async (credentials: LoginData) => {
    try {
      // 1. استدعاء API تسجيل الدخول للحصول على التوكن
      const response: AuthResponse = await apiService.auth.login(credentials); 

      // 2. حفظ التوكنين في التخزين المحلي
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);

      // 3. حفظ بيانات المستخدم الكاملة في localStorage
      const userData: CurrentUser = {
        id: response.user.id,
        username: response.user.username,
        email: response.user.email,
        profile: response.user.profile,
      };
      localStorage.setItem('user', JSON.stringify(userData));

      // 4. تحديث حالة المستخدم
      setUser(userData);
      
      // 5. التوجيه إلى لوحة التحكم
      navigate('/dashboard'); 

    } catch (error) {
      console.error("Login failed:", error);
      // مهم: إعادة طرح الخطأ ليتمكن مكون Signup من معالجته وعرض رسالة الخطأ للمستخدم
      throw error; 
    }
  };

  const contextValue: AuthContextType = {
    user,
    isLoggedIn: !!user,
    login,
    logout,
  };

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

// دالة Hook لاستخدام الـ Context
export const useAuth = () => {
  return useContext(AuthContext);
};