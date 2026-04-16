<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
    <div class="max-w-md w-full bg-white p-8 rounded-xl shadow-sm border border-gray-100">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold tracking-tight text-gray-900">Snip Share</h1>
      </div>
      
      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700">用户名</label>
          <input 
            v-model="form.username" 
            type="text" 
            required 
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 font-mono text-sm"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">密码</label>
          <input 
            v-model="form.password" 
            type="password" 
            required 
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 font-mono text-sm"
          />
        </div>
        
        <div v-if="errorMessage" class="text-red-500 text-sm text-center">
          {{ errorMessage }}
        </div>

        <button 
          type="submit" 
          :disabled="isLoading"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 disabled:opacity-50 transition-colors"
        >
          {{ isLoading ? '登录中...' : '进入终端' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { loginApi } from '../api/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ username: '', password: '' })
const isLoading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const res = await loginApi(form.username, form.password)
    authStore.login(res.access_token) // 存入 Pinia 和 localStorage
    router.push('/') // 跳转到首页
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '登录失败，请检查网络或凭证'
  } finally {
    isLoading.value = false
  }
}
</script>