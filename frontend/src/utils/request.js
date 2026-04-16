// src/utils/request.js
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'

const request = axios.create({
  baseURL: '/api', 
  timeout: 5000
})

request.interceptors.request.use(config => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers['Authorization'] = `Bearer ${authStore.token}`
  }
  return config
}, error => Promise.reject(error))

request.interceptors.response.use(response => {
  return response.data
}, error => {
  if (error.response) {
    const status = error.response.status
    if (status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.push('/login')
    } else if (status === 410) {
      // 优雅拦截墓碑模式，不抛出红色报错，而是返回特殊对象
      return Promise.resolve({ isTombstone: true, message: error.response.data.detail })
    }
  }
  return Promise.reject(error)
})

export default request