import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/api/auth/register', data),
  login: (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    return api.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getCurrentUser: () => api.get('/api/auth/me'),
  updateUser: (data) => api.put('/api/auth/me', data),
  changePassword: (data) => api.post('/api/auth/change-password', data),
};

export const incomeAPI = {
  create: (data) => api.post('/api/income', data),
  getLatest: () => api.get('/api/income/latest'),
};

export const expenseLimitAPI = {
  create: (data) => api.post('/api/expense-limits', data),
  getLatest: () => api.get('/api/expense-limits/latest'),
};

export const transactionAPI = {
  create: (data) => api.post('/api/transactions', data),
  getAll: () => api.get('/api/transactions'),
  delete: (id) => api.delete(`/api/transactions/${id}`),
};

export const budgetAPI = {
  generate: () => api.post('/api/budget/generate'),
  getAll: () => api.get('/api/budget'),
};

export const anomalyAPI = {
  detect: () => api.post('/api/anomalies/detect'),
  getAll: () => api.get('/api/anomalies'),
};

export const dashboardAPI = {
  getStats: (period = 'current_month') => api.get('/api/dashboard', { params: { period } }),
  getTrends: (period = 'current_month') => api.get('/api/dashboard/trends', { params: { period } }),
};

export const settingsAPI = {
  get: () => api.get('/api/settings'),
  update: (data) => api.put('/api/settings', data),
};

export const insightsAPI = {
  get: () => api.get('/api/insights'),
};

export default api;
