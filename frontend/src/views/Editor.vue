<template>
  <div class="h-screen flex flex-col bg-white">
    <div class="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
      <div class="flex-1 flex items-center gap-4">
        <button @click="$router.back()" class="text-gray-500 hover:text-gray-900">← 返回</button>
        <input 
          v-model="title" 
          placeholder="输入帖子标题..." 
          class="flex-1 bg-transparent border-none focus:outline-none text-lg font-bold font-sans placeholder-gray-400"
        />
      </div>
      <div class="flex items-center gap-4">
        <span v-if="isEditMode" class="text-xs text-blue-600 font-mono bg-blue-100 px-2 py-1 rounded">
          ✎ Editing
        </span>
        <span v-else-if="parentId" class="text-xs text-gray-500 font-mono bg-gray-200 px-2 py-1 rounded">
          ⑂ Forking...
        </span>
        
        <button 
          @click="savePost" 
          :disabled="isSaving || !title.trim()"
          class="px-6 py-2 bg-gray-900 text-white rounded-md font-medium text-sm hover:bg-gray-800 disabled:opacity-50"
        >
          {{ isSaving ? '处理中...' : (isEditMode ? '保存修改' : '发布 Snip') }}
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-hidden font-mono">
      <MdEditor v-model="content" language="zh-CN" theme="light" class="h-full" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MdEditor } from 'md-editor-v3'
// 导入 updatePost 接口
import { createPost, getPostById, updatePost } from '../api/posts'

const router = useRouter()
const route = useRoute()

const title = ref('')
const content = ref('')
const parentId = ref(null)
const isSaving = ref(false)

// 区分模式标识
const isEditMode = ref(false)
const targetEditId = ref(null)

onMounted(async () => {
  const forkId = route.query.fork_from
  const editId = route.query.edit
  
  if (editId) {
    isEditMode.value = true
    targetEditId.value = editId
    try {
      const originalPost = await getPostById(editId)
      title.value = originalPost.title
      content.value = originalPost.content
    } catch (e) {
      alert("无法拉取待编辑的帖子")
    }
  } else if (forkId) {
    try {
      const originalPost = await getPostById(forkId)
      title.value = `[Fork] ${originalPost.title}`
      content.value = originalPost.content
      parentId.value = forkId
    } catch (e) {
      console.warn("无法拉取被 Fork 的帖子内容")
    }
  }
})

const savePost = async () => {
  if (!title.value.trim()) return
  isSaving.value = true
  
  try {
    let resId;
    if (isEditMode.value) {
      // 发送 PUT 请求更新数据
      await updatePost(targetEditId.value, {
        title: title.value,
        content: content.value
      })
      resId = targetEditId.value
    } else {
      // 发送 POST 请求新建数据
      const res = await createPost({
        title: title.value,
        content: content.value,
        parent_id: parentId.value || null
      })
      resId = res.id
    }
    router.replace(`/post/${resId}`)
  } catch (error) {
    alert("操作失败: " + (error.response?.data?.detail || error.message))
  } finally {
    isSaving.value = false
  }
}
</script>