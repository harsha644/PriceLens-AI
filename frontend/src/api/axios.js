import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getStoredTokens = () => {
  const localAccess = localStorage.getItem('access_token');
  const localRefresh = localStorage.getItem('refresh_token');
  if (localAccess) {
    return { access: localAccess, refresh: localRefresh, storage: localStorage };
  }
  const sessionAccess = sessionStorage.getItem('access_token');
  const sessionRefresh = sessionStorage.getItem('refresh_token');
  if (sessionAccess) {
    return { access: sessionAccess, refresh: sessionRefresh, storage: sessionStorage };
  }
  return { access: null, refresh: null, storage: null };
};

export const setStoredTokens = (tokens, rememberMe = false) => {
  clearStoredTokens();
  const storage = rememberMe ? localStorage : sessionStorage;
  if (tokens.access) storage.setItem('access_token', tokens.access);
  if (tokens.refresh) storage.setItem('refresh_token', tokens.refresh);
  storage.setItem('remember_me', rememberMe ? 'true' : 'false');
};

export const clearStoredTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('remember_me');
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
  sessionStorage.removeItem('remember_me');
};

api.interceptors.request.use(
  (config) => {
    const { access } = getStoredTokens();
    if (access) {
      config.headers.Authorization = `Bearer ${access}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url.includes('/api/auth/login/') && !originalRequest.url.includes('/api/auth/refresh/')) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const { refresh, storage } = getStoredTokens();
      if (!refresh) {
        clearStoredTokens();
        window.dispatchEvent(new Event('auth:logout'));
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/api/auth/refresh/`, { refresh });
        const newAccess = response.data.access;
        if (storage) {
          storage.setItem('access_token', newAccess);
        }
        api.defaults.headers.common['Authorization'] = `Bearer ${newAccess}`;
        processQueue(null, newAccess);
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearStoredTokens();
        window.dispatchEvent(new Event('auth:logout'));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
