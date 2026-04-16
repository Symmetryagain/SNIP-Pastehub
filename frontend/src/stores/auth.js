// src/stores/auth.js
import { defineStore } from 'pinia'

// 简单的 JWT 解码函数（不验证签名，仅读取 payload）
function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
    return JSON.parse(jsonPayload)
  } catch (e) {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    // 解析出当前用户的 ID，方便后续鉴权判断
    userId: (state) => {
      if (!state.token) return null
      const payload = parseJwt(state.token)
      return payload ? payload.sub : null
    }
  },
  actions: {
    login(token) {
      this.token = token
      localStorage.setItem('token', token)
    },
    logout() {
      this.token = null
      localStorage.removeItem('token')
    }
  }
})