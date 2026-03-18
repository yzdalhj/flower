import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import TDesign from 'tdesign-vue-next'
import { MotionPlugin } from '@vueuse/motion'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

// 引入TDesign样式
import 'tdesign-vue-next/es/style/index.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(TDesign)
app.use(MotionPlugin)

// 初始化认证状态
const authStore = useAuthStore()
authStore.initAuth()

app.mount('#app')
