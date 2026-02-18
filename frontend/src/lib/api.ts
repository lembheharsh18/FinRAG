import axios from 'axios'
import { auth } from './firebase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to all requests
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - try to refresh
      const user = auth.currentUser
      if (user) {
        try {
          const token = await user.getIdToken(true) // Force refresh
          error.config.headers.Authorization = `Bearer ${token}`
          return api.request(error.config)
        } catch {
          // Refresh failed, redirect to login
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
