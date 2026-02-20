import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

// Decode JWT payload without verifying signature (verification happens on backend)
const decodeToken = (token) => {
  try {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    // Check expiry
    if (decoded.exp && decoded.exp * 1000 < Date.now()) return null;
    return { id: decoded.id, email: decoded.sub, name: decoded.name || '' };
  } catch {
    return null;
  }
};

export const AuthProvider = ({ children }) => {
  const [token] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('token');
    return saved ? decodeToken(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  // On mount: if token exists but is expired/invalid, log out
  useEffect(() => {
    const saved = localStorage.getItem('token');
    if (saved) {
      const decoded = decodeToken(saved);
      if (!decoded) {
        logout();
      }
    }
  }, []);

  const login = async (email, password) => {
    const response = await authAPI.login(email, password);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    const decoded = decodeToken(access_token);
    setUser(decoded);
  };

  const register = async (userData) => {
    const response = await authAPI.register(userData);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    const decoded = decodeToken(access_token);
    setUser(decoded);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const updateUser = async (userData) => {
    const response = await authAPI.updateUser(userData);
    setUser(response.data);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
