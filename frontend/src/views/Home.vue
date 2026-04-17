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

    <div v-if="!loading && availableTags.length > 0" class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div class="flex items-center gap-4 mb-3">
        <span class="text-sm font-medium text-gray-700 font-sans">Filter</span>
        <div class="flex bg-white rounded border border-gray-300 overflow-hidden text-xs font-mono font-bold cursor-pointer select-none">
          <div @click="filterMode = 'OR'" :class="['px-3 py-1 transition-colors', filterMode === 'OR' ? 'bg-gray-800 text-white' : 'text-gray-500 hover:bg-gray-100']">OR</div>
          <div @click="filterMode = 'AND'" :class="['px-3 py-1 transition-colors', filterMode === 'AND' ? 'bg-gray-800 text-white' : 'text-gray-500 hover:bg-gray-100']">AND</div>
        </div>
        <button v-if="selectedTags.length > 0" @click="selectedTags = []" class="text-xs text-gray-500 hover:text-gray-900 underline ml-auto">清除筛选</button>
      </div>
      <div class="flex flex-wrap gap-2">
        <button v-for="tag in availableTags" :key="tag" @click="toggleFilterTag(tag)" :class="['px-2.5 py-1 rounded-md text-xs font-mono transition-all border', selectedTags.includes(tag) ? 'bg-gray-800 text-white border-gray-800 shadow-sm' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400']">
          #{{ tag }}
        </button>
      </div>
    </div>
    <div v-if="loading" class="text-gray-500 font-mono text-sm animate-pulse">Fetching...</div>
    
    <div v-else class="space-y-4">
      <div 
        v-for="post in filteredPosts"
        :key="post.id"
        @click="$router.push(`/post/${post.id}`)"
        :class="[
          'block p-5 rounded-lg border transition-all group cursor-pointer',
          post.status === 'deleted' ? 'bg-gray-50 border-gray-200 opacity-60 grayscale' : 'bg-white border-gray-200 hover:border-gray-900 hover:shadow-md'
        ]"
      >
        <div class="flex justify-between items-start gap-4">
          <h2 class="text-lg font-semibold text-gray-900 leading-tight">
            <span v-if="post.status === 'deleted'" class="mr-2 text-gray-500">[已删除]</span>
            {{ post.title }}
          </h2>
          <span class="text-xs text-gray-400 font-mono shrink-0 pt-0.5">{{ formatListTime(post) }}</span>
        </div>
        
        <div class="mt-4 text-sm flex items-center justify-between border-t border-transparent group-hover:border-gray-50 pt-3 transition-colors">
          
          <div class="flex items-center gap-3 text-gray-600">
            <span class="font-bold">@{{ post.author?.username }}</span>
            <span v-if="post.parent_id" class="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs font-mono border border-blue-100">⑂ Forked</span>
          </div>
          
          <div class="flex items-center gap-3">
            
            <div v-if="canOperate(post)" class="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0">
              <button @click.stop="handleEdit(post.id)" class="p-1.5 bg-blue-50 text-blue-600 rounded hover:bg-blue-100" title="编辑">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              </button>
              <button v-if="post.status !== 'deleted'" @click.stop="handleDelete(post.id)" class="p-1.5 bg-red-50 text-red-600 rounded hover:bg-red-100" title="删除">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              </button>
            </div>

            <div class="flex items-center gap-1.5">
              <div v-if="post.tags && post.tags.length > 0" class="flex flex-wrap justify-end gap-1.5">
                <span 
                  v-for="tag in post.tags" 
                  :key="tag" 
                  :class="['px-2 py-0.5 border rounded-sm text-[11px] font-mono', getTagStyle(tag, post.status === 'deleted')]"
                >
                  {{ tag }}
                </span>
              </div>
              <span v-if="post.created_via !== 'web'" class="text-xs text-gray-400 font-mono ml-1">via {{ post.created_via }}</span>
            </div>

          </div>
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
import { getTagStyle, formatListTime } from '../utils/helpers'

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

const handleLogout = () => { authStore.logout(); router.push('/login') }
onMounted(fetchPosts)

// --- 筛选与标签色彩哈希引擎 ---
const selectedTags = ref([])
const filterMode = ref('OR')

const availableTags = computed(() => {
  const tagSet = new Set()
  posts.value.forEach(p => { if (p.tags) p.tags.forEach(t => tagSet.add(t)) })
  return Array.from(tagSet).sort()
})

const toggleFilterTag = (tag) => {
  if (selectedTags.value.includes(tag)) selectedTags.value = selectedTags.value.filter(t => t !== tag)
  else selectedTags.value.push(tag)
}

const filteredPosts = computed(() => {
  if (selectedTags.value.length === 0) return posts.value;
  return posts.value.filter(post => {
    const pTags = post.tags || []
    return filterMode.value === 'OR' 
      ? selectedTags.value.some(tag => pTags.includes(tag))
      : selectedTags.value.every(tag => pTags.includes(tag))
  })
})
</script>