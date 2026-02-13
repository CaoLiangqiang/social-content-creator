import { create } from 'zustand';
import api from '../utils/api';

const useAuthStore = create((set, get) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post('/users/login', { email, password });
      const { user, token } = response.data;
      
      localStorage.setItem('token', token);
      set({ user, token, isAuthenticated: true, isLoading: false });
      return { success: true };
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error.message || '登录失败',
        isAuthenticated: false 
      });
      return { success: false, error: error.message };
    }
  },

  register: async (username, email, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post('/users/register', { 
        username, 
        email, 
        password 
      });
      const { user, token } = response.data;
      
      localStorage.setItem('token', token);
      set({ user, token, isAuthenticated: true, isLoading: false });
      return { success: true };
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error.message || '注册失败',
        isAuthenticated: false 
      });
      return { success: false, error: error.message };
    }
  },

  logout: async () => {
    try {
      await api.post('/users/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      set({ 
        user: null, 
        token: null, 
        isAuthenticated: false,
        error: null 
      });
    }
  },

  fetchProfile: async () => {
    try {
      const response = await api.get('/users/profile');
      set({ user: response.data });
    } catch (error) {
      console.error('Fetch profile error:', error);
      if (error.status === 401) {
        get().logout();
      }
    }
  },

  clearError: () => set({ error: null })
}));

export { useAuthStore };
export default useAuthStore;
