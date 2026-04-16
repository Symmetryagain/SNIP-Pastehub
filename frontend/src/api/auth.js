// src/api/auth.js
import request from '../utils/request'

export function loginApi(username, password) {
  // FastAPI 强制要求 x-www-form-urlencoded 格式
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  
  return request.post('/auth/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
}