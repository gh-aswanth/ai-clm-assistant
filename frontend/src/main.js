import { createApp } from 'vue'
import { MotionPlugin } from '@vueuse/motion'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import { authStore } from './utils/auth'
import './style.css'

// Global 401 handler — only clear session when backend explicitly rejects our token
axios.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      const url = err.config?.url || ''
      // Only log out for auth-protected API calls, not public endpoints
      const isAuthCall = url.includes('/api/auth/') || url.includes('/api/contracts') ||
        url.includes('/api/templates') || url.includes('/api/guidelines') ||
        url.includes('/api/drive') || url.includes('/api/signers') ||
        url.includes('/api/dashboard')
      if (isAuthCall && window.location.pathname !== '/login') {
        authStore.logout()
        router.push('/login')
      }
    }
    return Promise.reject(err)
  }
)

createApp(App).use(router).use(MotionPlugin).mount('#app')
