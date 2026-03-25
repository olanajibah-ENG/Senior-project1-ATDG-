import axios, { type InternalAxiosRequestConfig, type AxiosResponse, type AxiosError } from 'axios';

const apiClient = axios.create({
    // Use environment variable or fallback to relative path for proxy
    baseURL: import.meta.env.VITE_API_URL || '/',
    timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
    headers: {
        'Content-Type': 'application/json',
    },
    // ✅ Enable credentials (cookies) for CORS requests - CRITICAL for CSRF tokens
    withCredentials: true,
});

// Flag to prevent infinite refresh loops
let isRefreshing = false;
let failedQueue: Array<{
    resolve: (value?: unknown) => void;
    reject: (error?: unknown) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

// Helper function to extract CSRF token from cookies
// ✅ تحسين: البحث عن token من عدة أسماء ممكنة
const getCsrfToken = () => {
  const cookies = document.cookie.split(';').map(c => c.trim());
  
  // ابحث أولاً عن ai_csrftoken (الأولوية للمخصص)
  let token = cookies.find(c => c.startsWith('ai_csrftoken='))?.split('=')[1];
  
  // لو مش موجود، جرب csrftoken العادي
  if (!token) {
    token = cookies.find(c => c.startsWith('csrftoken='))?.split('=')[1];
  }
  
  return token ? decodeURIComponent(token) : null;
};

// Request interceptor: Add access token and CSRF token to all requests
apiClient.interceptors.request.use(
    (config) => {
        // Log request for debugging
        console.log('API Request:', {
            method: config.method?.toUpperCase(),
            url: config.url,
            baseURL: config.baseURL,
            fullURL: `${config.baseURL}${config.url}`,
            hasData: !!config.data,
            dataType: config.data?.constructor?.name,
        });

        // Skip token injection for auth endpoints
        const authEndpoints = ['/login/', '/signup/', '/api/token/refresh/', '/auth/token/verify/'];
        const isAuthEndpoint = authEndpoints.some(endpoint => config.url?.includes(endpoint));

        // These endpoints use AllowAny on the backend.
        // Sending an expired/invalid token still triggers 401 — so skip Authorization entirely.
        const noAuthEndpoints = [
            '/api/analysis/reviewer/stats/',
            '/api/analysis/evaluation-stats/',
            '/api/analysis/ai-explanations/',
            '/api/analysis/reviewer/ai-tasks/',
            '/api/analysis/generated-files/',
            '/api/analysis/analysis-results/',
            '/api/analysis/analysis-jobs/',
            '/api/analysis/submit-human-review/',
        ];
        const isNoAuthEndpoint = noAuthEndpoints.some(ep => config.url?.includes(ep));

        // Add Authorization only for protected endpoints
        if (!isAuthEndpoint && !isNoAuthEndpoint) {
            const accessToken = localStorage.getItem('access_token');
            if (accessToken) {
                config.headers.Authorization = `Bearer ${accessToken}`;
                console.log('🔑 Added Authorization header for:', config.url);
            } else {
                console.warn('⚠️ No access token found in localStorage for:', config.url);
            }
        }

        // Add CSRF token if available - ✅ تحسين: دعم عدة أسماء للـ cookie
        const csrfToken = getCsrfToken();
        if (csrfToken && ['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
            config.headers['X-CSRFToken'] = csrfToken;
            console.log('CSRF header added →', csrfToken.substring(0, 8) + '...');
        }

        // ✅ تحسين: لا تعيّن Content-Type للـ FormData - يتم تعيينها تلقائياً مع الـ boundary
        if (config.data && !(config.data instanceof FormData) && !config.headers['Content-Type']) {
            config.headers['Content-Type'] = 'application/json';
        }

        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    }
);

// Response interceptor: Handle 401 errors and refresh tokens
apiClient.interceptors.response.use(
    (response: AxiosResponse) => {
        return response;
    },
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Handle 401 Unauthorized errors
        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
            // Skip refresh for auth endpoints
            const authEndpoints = ['/login/', '/signup/', '/api/token/refresh/', '/auth/token/verify/'];
            const isAuthEndpoint = authEndpoints.some(endpoint => originalRequest.url?.includes(endpoint));

            if (isAuthEndpoint) {
                return Promise.reject(error);
            }

            if (isRefreshing) {
                // If already refreshing, queue this request
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then((token) => {
                        if (originalRequest.headers) {
                            originalRequest.headers.Authorization = `Bearer ${token}`;
                        }
                        return apiClient(originalRequest);
                    })
                    .catch((err) => {
                        return Promise.reject(err);
                    });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            const refreshToken = localStorage.getItem('refresh_token');

            console.log('🔄 Token refresh attempt:', {
                hasRefreshToken: !!refreshToken,
                refreshTokenPreview: refreshToken ? `${refreshToken.substring(0, 20)}...` : 'none',
                originalUrl: originalRequest.url
            });

            if (!refreshToken) {
                // No refresh token, logout user
                processQueue(error, null);
                isRefreshing = false;
                handleLogout();
                return Promise.reject(error);
            }

            try {
                // Create a fresh axios instance for token refresh to avoid interceptor recursion
                const refreshClient = axios.create({
                    baseURL: import.meta.env.VITE_API_URL || '/',
                    timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    withCredentials: true,
                });

                // Add CSRF token to refresh request
                const csrfToken = getCsrfToken();
                if (csrfToken) {
                    refreshClient.defaults.headers['X-CSRFToken'] = csrfToken;
                }

                // Attempt to refresh the token
                const response = await refreshClient.post<{ access: string }>(
                    '/api/token/refresh/',
                    { refresh: refreshToken }
                );

                console.log('✅ Token refresh successful:', {
                    status: response.status,
                    hasAccessToken: !!response.data.access,
                    tokenPreview: response.data.access ? `${response.data.access.substring(0, 20)}...` : 'none'
                });

                const { access } = response.data;

                // Update access token in localStorage
                localStorage.setItem('access_token', access);

                // Update the original request with new token
                if (originalRequest.headers) {
                    originalRequest.headers.Authorization = `Bearer ${access}`;
                }

                // Process queued requests
                processQueue(null, access);
                isRefreshing = false;

                // Retry the original request
                return apiClient(originalRequest);
            } catch (refreshError) {
                console.error('❌ Token refresh failed:', {
                    error: refreshError,
                    status: (refreshError as any)?.response?.status,
                    statusText: (refreshError as any)?.response?.statusText,
                    data: (refreshError as any)?.response?.data
                });

                // Refresh failed, logout user
                processQueue(refreshError as AxiosError, null);
                isRefreshing = false;
                handleLogout();
                return Promise.reject(refreshError);
            }
        }

        // Better error logging for debugging
        if (error.response) {
            console.error('API Error:', {
                status: error.response.status,
                statusText: error.response.statusText,
                url: error.config?.url,
                data: error.response.data,
            });
        } else if (error.request) {
            console.error('Network Error:', {
                message: error.message,
                url: error.config?.url,
            });
        } else {
            console.error('Error:', error.message);
        }

        return Promise.reject(error);
    }
);

// Helper function to handle logout
const handleLogout = () => {
    // Clear all auth data (both possible token names)
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');

    // Dispatch custom event for AuthContext to handle
    window.dispatchEvent(new CustomEvent('auth:logout'));
};

export default apiClient;