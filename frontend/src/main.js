// src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// 引入 v4 全局 CSS
import './assets/style.css'
// 引入 md-editor-v3 的全局样式
import 'md-editor-v3/lib/style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')