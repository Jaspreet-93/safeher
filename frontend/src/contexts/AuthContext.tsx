import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '../types';

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user_id: string;
  email: string;
  role: 'user' | 'org_admin' | 'coordinator' | 'admin';
  full_name: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('safeher_access_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('safeher_user');
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem('safeher_user');
      }
    }
    setLoading(false);
  }, [token]);

  const login = async (email: string, password: string) => {
    const res = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.message || 'Authentication failed. Please verify credentials.');
    }

    const data: AuthResponse = await res.json();
    setToken(data.access_token);
    localStorage.setItem('safeher_access_token', data.access_token);
    localStorage.setItem('safeher_refresh_token', data.refresh_token);

    const loggedUser: User = {
      id: data.user_id,
      email: data.email,
      role: data.role,
    };
    setUser(loggedUser);
    localStorage.setItem('safeher_user', JSON.stringify(loggedUser));
  };

  const register = async (registerData: any) => {
    const res = await fetch('http://localhost:8000/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(registerData),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.message || 'Registration failed. Please check your details.');
    }

    const data: AuthResponse = await res.json();
    setToken(data.access_token);
    localStorage.setItem('safeher_access_token', data.access_token);
    localStorage.setItem('safeher_refresh_token', data.refresh_token);

    const newUser: User = {
      id: data.user_id,
      email: data.email,
      role: data.role,
    };
    setUser(newUser);
    localStorage.setItem('safeher_user', JSON.stringify(newUser));
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('safeher_refresh_token');
    if (refreshToken) {
      fetch('http://localhost:8000/api/v1/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      }).catch(() => {});
    }

    setUser(null);
    setToken(null);
    localStorage.removeItem('safeher_access_token');
    localStorage.removeItem('safeher_refresh_token');
    localStorage.removeItem('safeher_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
      }}
    >
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
