import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

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
  register: (data) => api.post('/auth/register', data),
  login: (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getCurrentUser: () => api.get('/auth/me'),
  updateUser: (data) => api.put('/auth/me', data),
  changePassword: (data) => api.post('/auth/change-password', data),
};

export const incomeAPI = {
  create: (data) => api.post('/income', data),
  getLatest: () => api.get('/income/latest'),
};

export const expenseLimitAPI = {
  create: (data) => api.post('/expense-limits', data),
  getLatest: () => api.get('/expense-limits/latest'),
};

export const transactionAPI = {
  create: (data) => api.post('/transactions', data),
  getAll: () => api.get('/transactions'),
  delete: (id) => api.delete(`/transactions/${id}`),
};

export const budgetAPI = {
  generate: () => api.post('/budget/generate'),
  getAll: () => api.get('/budget'),
};

export const anomalyAPI = {
  detect: () => api.post('/anomalies/detect'),
  getAll: () => api.get('/anomalies'),
};

export const dashboardAPI = {
  getStats: (period = 'current_month') => api.get('/dashboard', { params: { period } }),
  getTrends: (period = 'current_month') => api.get('/dashboard/trends', { params: { period } }),
};

export const settingsAPI = {
  get: () => api.get('/settings'),
  update: (data) => api.put('/settings', data),
};

export const insightsAPI = {
  get: () => api.get('/insights'),
};

export default api;
