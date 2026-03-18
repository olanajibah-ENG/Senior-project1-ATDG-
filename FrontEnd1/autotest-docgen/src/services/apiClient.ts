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
const getCsrfToken = (names = ['ai_csrftoken', 'csrftoken']): string | null => {
    const cookies = document.cookie.split(';');

    for (const name of names) {
        const nameEQ = name + '=';
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(nameEQ)) {
                // Decode the value in case it's URL-encoded
                return decodeURIComponent(cookie.substring(nameEQ.length));
            }
        }
    }
    return null;
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

        // Always add Authorization for AI endpoints
        const isAiEndpoint = config.url?.includes('/api/analysis/ai-explanations/') ||
            config.url?.includes('/api/analysis/');

        if (!isAuthEndpoint || isAiEndpoint) {
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
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken;
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

            if (!refreshToken) {
                // No refresh token, logout user
                processQueue(error, null);
                isRefreshing = false;
                handleLogout();
                return Promise.reject(error);
            }

            try {
                // Attempt to refresh the token using apiClient instead of axios directly
                // This ensures CSRF token is included for token refresh endpoint
                const response = await apiClient.post<{ access: string }>(
                    '/token/refresh/',
                    { refresh: refreshToken }
                );

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