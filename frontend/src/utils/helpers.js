// src/utils/helpers.js

// 1. 全局默认标签池
export const DEFAULT_TAGS = ['Theory', 'Snippet', 'Bug', 'Note', 'Idea', 'Life'];

// 2. 标签色彩哈希算法
export const getTagStyle = (tag, isDeleted = false) => {
  if (isDeleted) return 'bg-gray-50 text-gray-400 border-gray-200';
  const colors = [
    'bg-blue-50 text-blue-600 border-blue-100',
    'bg-emerald-50 text-emerald-600 border-emerald-100',
    'bg-purple-50 text-purple-600 border-purple-100',
    'bg-amber-50 text-amber-600 border-amber-100',
    'bg-rose-50 text-rose-600 border-rose-100',
    'bg-indigo-50 text-indigo-600 border-indigo-100',
    'bg-sky-50 text-sky-600 border-sky-100'
  ];
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
};

// 3. 主页列表专用：短格式 (例如: 4/18 19:20)
export const formatListTime = (post) => {
  if (!post || !post.created_at) return '';
  const formatShort = (s) => new Date(s + 'Z').toLocaleString('zh-CN', {hour12:false}).slice(5, -3);
  
  const cTime = formatShort(post.created_at);
  if (post.updated_at) {
    if (new Date(post.updated_at + 'Z').getTime() - new Date(post.created_at + 'Z').getTime() > 2000) {
      return `${cTime}, updated ${formatShort(post.updated_at)}`;
    }
  }
  return cTime;
};

// 4. 详情页专用：长格式 (例如: 2026/4/18 19:20:00)
export const formatDetailTime = (post) => {
  if (!post || !post.created_at) return '';
  const cTime = new Date(post.created_at + 'Z');
  const uTime = new Date(post.updated_at + 'Z');
  const cStr = cTime.toLocaleString();
  
  if (post.updated_at && (uTime.getTime() - cTime.getTime() > 2000)) {
    return `${cStr}, last updated on ${uTime.toLocaleString()}`;
  }
  return cStr;
};