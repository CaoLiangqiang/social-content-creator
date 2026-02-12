import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../utils/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false,
      error: null,

      login: async (email, password) => {
        set({ loading: true, error: null })
        try {
          const response = await api.post('/users/login', { email, password })
          const { user, token } = response.data.data
          set({ 
            user, 
            token, 
            isAuthenticated: true, 
            loading: false 
          })
          return { success: true }
        } catch (error) {
          const message = error.response?.data?.error || '登录失败'
          set({ error: message, loading: false })
          return { success: false, error: message }
        }
      },

      register: async (username, email, password) => {
        set({ loading: true, error: null })
        try {
          const response = await api.post('/users/register', { username, email, password })
          const { user, token } = response.data.data
          set({ 
            user, 
            token, 
            isAuthenticated: true, 
            loading: false 
          })
          return { success: true }
        } catch (error) {
          const message = error.response?.data?.error || '注册失败'
          set({ error: message, loading: false })
          return { success: false, error: message }
        }
      },

      logout: async () => {
        try {
          await api.post('/users/logout')
        } catch (error) {
          console.error('Logout error:', error)
        }
        set({ 
          user: null, 
          token: null, 
          isAuthenticated: false 
        })
      },

      getProfile: async () => {
        try {
          const response = await api.get('/users/profile')
          set({ user: response.data.data })
        } catch (error) {
        }
      },

      clearError: () => set({ error: null })
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        token: state.token,
        isAuthenticated: state.isAuthenticated 
      })
    }
  )
)
