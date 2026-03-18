import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('@/views/LandingView.vue'),
    meta: { public: true },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/chat/ChatView.vue'),
    meta: { public: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    redirect: '/admin/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { title: '仪表盘', icon: 'dashboard' },
      },
      {
        path: 'memories',
        name: 'Memories',
        component: () => import('@/views/admin/MemoriesView.vue'),
        meta: { title: '记忆管理', icon: 'store' },
      },
      {
        path: 'conversations',
        name: 'Conversations',
        component: () => import('@/views/admin/ConversationsView.vue'),
        meta: { title: '对话记录', icon: 'chat' },
      },

      {
        path: 'personality',
        name: 'Personality',
        component: () => import('@/views/admin/PersonalityView.vue'),
        meta: { title: '人格引擎', icon: 'user-circle' },
      },
      {
        path: 'statistics',
        name: 'Statistics',
        meta: { title: '统计管理', icon: 'chart' },
        children: [
          {
            path: 'llm-usage',
            name: 'LLMUsage',
            component: () => import('@/views/admin/LLMUsageView.vue'),
            meta: { title: 'LLM使用统计', icon: 'chart-line' },
          },
        ],
      },
      {
        path: 'system',
        name: 'System',
        meta: { title: '系统管理', icon: 'setting' },
        children: [
          {
            path: 'prompt-templates',
            name: 'PromptTemplates',
            component: () => import('@/views/admin/PromptTemplatesView.vue'),
            meta: { title: 'Prompt模板', icon: 'file-edit' },
          },
          {
            path: 'settings',
            name: 'Settings',
            component: () => import('@/views/admin/SettingsView.vue'),
            meta: { title: '系统设置', icon: 'tools-circle-filled' },
          },
          {
            path: 'accounts',
            name: 'Accounts',
            component: () => import('@/views/admin/AccountsView.vue'),
            meta: { title: '账号管理', icon: 'user' },
          },
          {
            path: 'users',
            name: 'Users',
            component: () => import('@/views/admin/UsersView.vue'),
            meta: { title: '用户管理', icon: 'member' },
          },
        ],
      },
    ],
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true, guestOnly: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 公开页面直接放行
  if (to.meta.public && !to.meta.guestOnly) {
    next()
    return
  }

  // 仅限游客访问的页面（如登录页），已登录则跳转
  if (to.meta.guestOnly && authStore.isLoggedIn) {
    next('/admin')
    return
  }

  // 需要认证的页面
  if (to.meta.requiresAuth || to.path.startsWith('/admin')) {
    // 如果没有 token，跳转到登录页
    if (!authStore.isLoggedIn) {
      next({
        path: '/login',
        query: { redirect: to.fullPath },
      })
      return
    }

    // 如果有 token 但没有用户信息，尝试获取用户信息
    if (!authStore.user) {
      const success = await authStore.fetchUserInfo()
      if (!success) {
        next({
          path: '/login',
          query: { redirect: to.fullPath },
        })
        return
      }
    }
  }

  next()
})

export default router
