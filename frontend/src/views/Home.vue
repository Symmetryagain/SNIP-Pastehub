<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="flex justify-between items-center mb-8 border-b pb-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Recent Snips</h1>
      </div>
      <div class="flex items-center gap-3">
        <button @click="handleLogout" class="px-4 py-2 text-gray-600 bg-gray-100 rounded-md text-sm font-medium hover:bg-gray-200 transition-colors">登出</button>
        <button @click="$router.push('/editor')" class="px-4 py-2 bg-gray-900 text-white rounded-md text-sm font-medium hover:bg-gray-800 transition-colors">+ 新建</button>
      </div>
    </div>

    <div v-if="loading" class="text-gray-500 font-mono text-sm animate-pulse">Fetching...</div>
    
    <div v-else class="space-y-4">
      <div 
        v-for="post in posts" 
        :key="post.id"
        @click="$router.push(`/post/${post.id}`)"
        :class="[
          'relative block p-5 rounded-lg border transition-all group cursor-pointer',
          post.status === 'deleted' ? 'bg-gray-50 border-gray-200 opacity-60 grayscale' : 'bg-white border-gray-200 hover:border-gray-900 hover:shadow-md'
        ]"
      >
        <div 
          v-if="canOperate(post)" 
          class="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <button @click.stop="handleEdit(post.id)" class="p-1.5 bg-blue-50 text-blue-600 rounded hover:bg-blue-100" title="编辑">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button v-if="post.status !== 'deleted'" @click.stop="handleDelete(post.id)" class="p-1.5 bg-red-50 text-red-600 rounded hover:bg-red-100" title="删除">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>

        <div class="flex justify-between items-start pr-16">
          <h2 class="text-lg font-semibold text-gray-900">
            <span v-if="post.status === 'deleted'" class="mr-2">[已删除]</span>
            {{ post.title }}
          </h2>
          <span class="text-xs text-gray-400 font-mono shrink-0">{{ formatDetailedTime(post) }}</span>
        </div>
        
        <div class="mt-3 text-sm flex items-center justify-between">
          <div class="flex items-center gap-3 text-gray-600">
            <span class="font-bold">@{{ post.author?.username }}</span>
            <span v-if="post.parent_id" class="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs font-mono">⑂ Forked</span>
          </div>
          <span v-if="post.created_via !== 'web'" class="text-xs text-gray-400 font-mono">via {{ post.created_via }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getPosts, deletePost } from '../api/posts'

const router = useRouter()
const authStore = useAuthStore()

const posts = ref([])
const loading = ref(true)

const isAdmin = computed(() => authStore.token && JSON.parse(atob(authStore.token.split('.')[1])).username === 'admin')

const canOperate = (post) => {
  // 如果帖子已经删了，谁都不能再编辑或删除
  if (post.status === 'deleted') return false;
  
  // 否则，只有作者本人或 admin 可以操作
  return authStore.userId === post.author_id || isAdmin.value;
}

const fetchPosts = async () => {
  try {
    posts.value = await getPosts()
  } catch (error) { console.error(error) }
  finally { loading.value = false }
}

const handleEdit = (id) => router.push(`/editor?edit=${id}`)

const handleDelete = async (id) => {
  if (confirm('确定要删除吗？')) {
    try {
      await deletePost(id)
      await fetchPosts() // 刷新列表
    } catch (e) { alert("无权操作") }
  }
}

const formatTime = (s) => s ? new Date(s + 'Z').toLocaleString('zh-CN', {hour12:false}).slice(5, -3) : ''
const formatDetailedTime = (p) => {
  const c = formatTime(p.created_at)
  if (new Date(p.updated_at + 'Z') - new Date(p.created_at + 'Z') > 2000) {
    return `${c}, updated ${formatTime(p.updated_at)}`
  }
  return c
}

const handleLogout = () => { authStore.logout(); router.push('/login') }
onMounted(fetchPosts)
</script>