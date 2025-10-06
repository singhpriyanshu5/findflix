import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface User {
  id: string;
  name: string;
  email: string;
  picture?: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (name: string, email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  processOAuthSession: (sessionId: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Check for existing session on app start
  useEffect(() => {
    checkExistingSession();
  }, []);

  const checkExistingSession = async () => {
    try {
      const sessionToken = await AsyncStorage.getItem('session_token');
      if (sessionToken) {
        // Set axios default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${sessionToken}`;
        
        // Verify session with backend
        const response = await axios.get(`${BACKEND_URL}/api/auth/me`);
        setUser(response.data);
      }
    } catch (error) {
      console.error('Session check failed:', error);
      // Clear invalid token
      await AsyncStorage.removeItem('session_token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      console.log('Attempting login with backend URL:', BACKEND_URL);
      
      const response = await axios.post(`${BACKEND_URL}/api/auth/login`, {
        email,
        password,
      });

      console.log('Login response:', response.data);
      const { user: userData, session_token } = response.data;
      
      // Store session token
      await AsyncStorage.setItem('session_token', session_token);
      
      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${session_token}`;
      
      setUser(userData);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      console.error('Error details:', error.response?.data);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (name: string, email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/auth/register`, {
        name,
        email,
        password,
      });

      const { user: userData, session_token } = response.data;
      
      // Store session token
      await AsyncStorage.setItem('session_token', session_token);
      
      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${session_token}`;
      
      setUser(userData);
      return true;
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const processOAuthSession = async (sessionId: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      const response = await axios.post(
        `${BACKEND_URL}/api/auth/oauth/session`,
        {},
        {
          headers: {
            'X-Session-ID': sessionId,
          },
        }
      );

      const { user: userData, session_token } = response.data;
      
      // Store session token
      await AsyncStorage.setItem('session_token', session_token);
      
      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${session_token}`;
      
      setUser(userData);
      return true;
    } catch (error) {
      console.error('OAuth session processing failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Call backend logout
      await axios.post(`${BACKEND_URL}/auth/logout`);
    } catch (error) {
      console.error('Logout API failed:', error);
    } finally {
      // Clear local session regardless of API call result
      await AsyncStorage.removeItem('session_token');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    processOAuthSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};