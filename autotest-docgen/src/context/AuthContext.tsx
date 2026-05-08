import React, { createContext, useState, useContext, type ReactNode, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService, { type LoginData, type AuthResponse, type CurrentUser } from '../services/api.service';

const decodeJWT = (token: string) => {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
};

const navigateByRole = (roleType: string | undefined, navigate: Function) => {
  switch (roleType?.toLowerCase()) {
    case 'admin':    navigate('/admin');     break;
    case 'reviewer': navigate('/reviewer'); break;
    default:         navigate('/dashboard'); break;
  }
};

interface AuthContextType {
  user: CurrentUser | null;
  isLoggedIn: boolean;
  login: (credentials: LoginData) => Promise<void>;
  logout: () => void;
}

const defaultAuthContext: AuthContextType = {
  user: null,
  isLoggedIn: false,
  login: () => Promise.resolve(),
  logout: () => { },
};

export const AuthContext = createContext<AuthContextType>(defaultAuthContext);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState<CurrentUser | null>(null);

  const loadUserFromStorage = useCallback(() => {
    try {
      const storedUser = localStorage.getItem('user');
      const accessToken = localStorage.getItem('access_token');

      if (storedUser && accessToken) {
        const userData: CurrentUser = JSON.parse(storedUser);
        setUser(userData);

        const currentPath = window.location.pathname;
        if (currentPath === '/' || currentPath === '/auth') {
          const decoded = decodeJWT(accessToken);
          navigateByRole(decoded?.role_type, navigate);
        }
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Error loading user from storage:', error);
      setUser(null);
    }
  }, [navigate]);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    navigate('/auth');
  }, [navigate]);

  useEffect(() => {
    loadUserFromStorage();

    const handleLogoutEvent = () => {
      logout();
    };

    window.addEventListener('auth:logout', handleLogoutEvent);

    return () => {
      window.removeEventListener('auth:logout', handleLogoutEvent);
    };
  }, [logout]);

  const login = async (credentials: LoginData) => {
    try {
      const response: AuthResponse = await apiService.auth.login(credentials);

      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);

      const userData: CurrentUser = {
        id: response.user.id,
        username: response.user.username,
        email: response.user.email,
        profile: response.user.profile,
      };
      localStorage.setItem('user', JSON.stringify(userData));

      setUser(userData);

      const decoded = decodeJWT(response.access);
      navigateByRole(decoded?.role_type, navigate);

    } catch (error) {
      console.error('Login failed:', error);
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

export const useAuth = () => {
  return useContext(AuthContext);
};