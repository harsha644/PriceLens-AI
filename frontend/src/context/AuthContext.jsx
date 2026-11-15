import React, { createContext, useContext, useState, useEffect } from 'react';
import api, { getStoredTokens, setStoredTokens, clearStoredTokens } from '../api/axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [demoMode, setDemoMode] = useState(true); // Enabled by default so users can immediately test all features

  const fetchProfile = async () => {
    try {
      const res = await api.get('/api/auth/profile/');
      setUser(res.data);
    } catch (err) {
      setUser(null);
      clearStoredTokens();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const { access } = getStoredTokens();
    if (access) {
      fetchProfile();
    } else {
      setLoading(false);
    }

    const handleLogoutEvent = () => {
      setUser(null);
      clearStoredTokens();
    };

    window.addEventListener('auth:logout', handleLogoutEvent);
    return () => window.removeEventListener('auth:logout', handleLogoutEvent);
  }, []);

  const login = async (usernameOrEmail, password, rememberMe = false) => {
    const res = await api.post('/api/auth/login/', {
      username_or_email: usernameOrEmail,
      password,
      remember_me: rememberMe,
    });
    setStoredTokens(res.data.tokens, rememberMe);
    setUser(res.data.user);
    return res.data;
  };

  const register = async (userData) => {
    const res = await api.post('/api/auth/register/', userData);
    setStoredTokens(res.data.tokens, true);
    setUser(res.data.user);
    return res.data;
  };

  const logout = async () => {
    const { refresh } = getStoredTokens();
    if (refresh) {
      try {
        await api.post('/api/auth/logout/', { refresh });
      } catch (e) {
        // Continue logout locally even if backend blacklist returns error
      }
    }
    clearStoredTokens();
    setUser(null);
  };

  const updateProfile = async (profileData) => {
    const res = await api.put('/api/auth/profile/', profileData);
    setUser(res.data);
    return res.data;
  };

  const changePassword = async (data) => {
    const res = await api.post('/api/auth/change-password/', data);
    return res.data;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        demoMode,
        setDemoMode,
        login,
        register,
        logout,
        updateProfile,
        changePassword,
        fetchProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
