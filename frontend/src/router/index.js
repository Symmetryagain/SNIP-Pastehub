// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  // 这些页面我们在下一阶段写，先占位
  { path: '/', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/post/:id', name: 'PostDetail', component: () => import('../views/PostDetail.vue') },
  { path: '/editor', name: 'Editor', component: () => import('../views/Editor.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：强制登录校验
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.name !== 'Login' && !authStore.isAuthenticated) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router