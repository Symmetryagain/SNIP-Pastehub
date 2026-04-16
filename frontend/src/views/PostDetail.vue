<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="mb-6">
      <button @click="$router.push('/')" class="text-gray-500 hover:text-gray-900 text-sm font-medium transition-colors">
        ← Back to List
      </button>
    </div>

    <div v-if="loading" class="text-gray-500 font-mono animate-pulse">Resolving AST...</div>

    <div v-else-if="isTombstone" class="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center mt-12 shadow-inner">
      <h2 class="text-3xl font-bold text-gray-400 mb-3 font-mono">410 GONE</h2>
      <p class="text-gray-500 font-sans">这段笔记已被原作者彻底移除。</p>
      <p class="text-xs text-gray-400 font-mono mt-6">/* The monument remains, but the data is freed. */</p>
    </div>

    <div v-else-if="post">
      <div class="border-b border-gray-200 pb-6 mb-6 flex flex-col md:flex-row md:justify-between md:items-start gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-900 mb-3">{{ post.title }}</h1>
          <div class="text-sm text-gray-500 flex flex-wrap items-center gap-x-4 gap-y-2 font-mono">
            <span class="font-bold text-gray-700">@{{ post.author?.username || 'Unknown' }}</span>
            
            <span>{{ formatDetailedTime(post) }}</span>
            
            <router-link 
              v-if="post.parent_id" 
              :to="`/post/${post.parent_id}`" 
              class="text-blue-600 hover:text-blue-800 hover:underline bg-blue-50 px-2 py-0.5 rounded transition-colors"
            >
              ⑂ Forked from {{ post.parent_id.substring(0, 8) }}
            </router-link>
          </div>
        </div>
        
        <div class="flex items-center gap-2 shrink-0">
			<button @click="copyMarkdown" class="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm font-medium hover:bg-gray-200 transition-colors">
				{{ isCopied ? '已复制' : '复制源码' }}
			</button>
			
			<template v-if="post.status !== 'deleted'">
				<button @click="handleFork" class="px-3 py-1.5 border border-gray-300 text-gray-700 rounded text-sm font-medium hover:bg-gray-50 transition-colors">
				⑂ Fork
				</button>
				
				<template v-if="isAuthor || isAdmin">
				<button @click="handleEdit" class="px-3 py-1.5 border border-blue-200 text-blue-600 rounded text-sm font-medium hover:bg-blue-50 transition-colors">
					编辑
				</button>
				<button @click="handleDelete" class="px-3 py-1.5 border border-red-200 text-red-600 rounded text-sm font-medium hover:bg-red-50 transition-colors">
					删除
				</button>
				</template>
			</template>

			<span v-else class="px-3 py-1.5 bg-gray-200 text-gray-500 rounded text-sm font-mono font-bold select-none">
				READ ONLY (ARCHIVED)
			</span>
		</div>
      </div>

      <div class="bg-white rounded-lg p-2 sm:p-6 shadow-sm border border-gray-100">
         <MdPreview :modelValue="post.content" language="zh-CN" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MdPreview } from 'md-editor-v3'
import { useAuthStore } from '../stores/auth'
import { getPostById, deletePost } from '../api/posts'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const post = ref(null)
const loading = ref(true)
const isTombstone = ref(false)
const isCopied = ref(false)

// 判断当前登录用户是否是帖子作者
const isAuthor = computed(() => {
  return post.value && authStore.userId === post.value.author_id
})

const isAdmin = computed(() => {
  if (!authStore.token) return false;
  try {
    const payload = JSON.parse(atob(authStore.token.split('.')[1]));
    return payload.username === 'admin';
  } catch {
    return false;
  }
});

// 时间格式化：如果被修改过，补充 last updated
const formatDetailedTime = (p) => {
  const cTime = new Date(p.created_at + 'Z')
  const uTime = new Date(p.updated_at + 'Z')
  const cStr = cTime.toLocaleString()
  
  // 判断是否有更新（防止创建时的微秒误差，判断差值是否大于2秒）
  if (uTime.getTime() - cTime.getTime() > 2000) {
    return `${cStr}, last updated on ${uTime.toLocaleString()}`
  }
  return cStr
}

const loadPost = async () => {
  loading.value = true
  isTombstone.value = false
  try {
    const res = await getPostById(route.params.id)
    
    // 逻辑调整：如果收到 410，只有非 admin 才会看到墓碑
    // 注意：由于我们修改了后端，admin 访问已删贴现在返回的是 200 而不是 410
    // 所以这里的判断逻辑主要是针对普通用户
    if (res.isTombstone) {
      isTombstone.value = true
    } else {
      post.value = res
    }
  } catch (error) {
    // 处理 admin 场景下后端返回的正常数据
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 核心修复：监听路由参数变化。如果用户在详情页点击了 Fork 父节点的链接，强制重新拉取数据
watch(() => route.params.id, (newId) => {
  if (newId) loadPost()
})

const copyMarkdown = async () => {
  try {
    await navigator.clipboard.writeText(post.value.content)
    isCopied.value = true
    setTimeout(() => { isCopied.value = false }, 2000)
  } catch (err) {
    alert('复制失败')
  }
}

const handleFork = () => router.push(`/editor?fork_from=${post.value.id}`)
const handleEdit = () => router.push(`/editor?edit=${post.value.id}`)

const handleDelete = async () => {
  if (confirm('确定要移除此内容吗？')) {
    try {
      await deletePost(post.value.id)
      isTombstone.value = true
    } catch (error) {
      alert("删除失败，可能您无权操作")
    }
  }
}

onMounted(loadPost)
</script>

<style>
.md-editor-preview pre { position: relative; }
</style>