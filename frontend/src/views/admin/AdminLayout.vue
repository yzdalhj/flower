<template>
  <t-layout class="admin-layout">
    <!-- 侧边栏 -->
    <t-aside class="admin-sidebar">
      <div class="sidebar-header">
        <div class="brand" @click="goHome">
          <span class="brand-icon">🌸</span>
          <span class="brand-text">AI小花</span>
        </div>
        <div class="brand-subtitle">管理后台</div>
      </div>

      <t-menu
        theme="light"
        :value="activeMenu"
        @change="handleMenuChange"
        class="admin-menu"
      >
        <template v-for="item in menuRoutes" :key="item.path">
          <t-submenu v-if="item.children && item.children.length > 0" :value="item.path">
            <template #icon>
              <t-icon :name="(item.meta?.icon as string) || 'file'" />
            </template>
            <template #title>{{ item.meta?.title }}</template>
            <t-menu-item
              v-for="child in item.children"
              :key="child.path"
              :value="`${item.path}/${child.path}`"
            >
              <template #icon>
                <t-icon :name="(child.meta?.icon as string) || 'file'" />
              </template>
              {{ child.meta?.title }}
            </t-menu-item>
          </t-submenu>
          <t-menu-item
            v-else
            :key="item.path"
            :value="item.path"
          >
            <template #icon>
              <t-icon :name="(item.meta?.icon as string) || 'file'" />
            </template>
            {{ item.meta?.title }}
          </t-menu-item>
        </template>
      </t-menu>

      <div class="sidebar-footer">
        <t-button block variant="text" @click="goToChat">
          <template #icon><t-icon name="chat" /></template>
          返回聊天
        </t-button>
      </div>
    </t-aside>

    <!-- 主内容区 -->
    <t-layout class="admin-main">
      <!-- 顶部栏 -->
      <t-header class="admin-header">
        <div class="header-left">
          <t-breadcrumb>
            <t-breadcrumb-item>管理后台</t-breadcrumb-item>
            <t-breadcrumb-item>{{ pageTitle }}</t-breadcrumb-item>
          </t-breadcrumb>
        </div>
        <div class="header-right">
          <t-button theme="default" variant="text" shape="square">
            <t-icon name="notification" />
          </t-button>
          <t-dropdown
            :options="userOptions"
            :min-column-width="120"
            @click="handleUserAction"
          >
            <t-button theme="default" variant="text">
              <template #icon><t-icon name="user" /></template>
              <span class="username">{{ authStore.username }}</span>
              <t-tag
                size="small"
                :theme="authStore.isSuperAdmin ? 'danger' : authStore.isAdmin ? 'primary' : 'default'"
                class="role-tag"
              >
                {{ authStore.userRole }}
              </t-tag>
              <t-icon name="chevron-down" />
            </t-button>
          </t-dropdown>
        </div>
      </t-header>

      <!-- 内容区 -->
      <t-content class="admin-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </t-content>
    </t-layout>
  </t-layout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { routes } from '@/router'
import { useAuthStore } from '@/stores/auth'
import { MessagePlugin } from 'tdesign-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 从路由配置获取 admin 子路由
const adminRoute = routes.find((r: RouteRecordRaw) => r.path === '/admin')
const menuRoutes = computed<RouteRecordRaw[]>(() => {
  if (!adminRoute || !adminRoute.children) return []
  return adminRoute.children.filter((child: RouteRecordRaw) => child.meta?.title)
})

// 当前激活的菜单
const activeMenu = computed(() => {
  // 遍历所有菜单和子菜单找到匹配的
  for (const item of menuRoutes.value) {
    if (item.children && item.children.length > 0) {
      for (const child of item.children) {
        if (route.path === `/admin/${item.path}/${child.path}`) {
          return `${item.path}/${child.path}`
        }
      }
    }
    if (route.path.includes(`/admin/${item.path}`)) {
      return item.path
    }
  }
  return 'dashboard'
})

// 页面标题
const pageTitle = computed(() => {
  // 遍历所有菜单和子菜单找到匹配的
  for (const item of menuRoutes.value) {
    if (item.children && item.children.length > 0) {
      for (const child of item.children) {
        if (route.path === `/admin/${item.path}/${child.path}`) {
          return child.meta?.title as string
        }
      }
    }
    if (item.path === activeMenu.value) {
      return (item.meta?.title as string) || '仪表盘'
    }
  }
  return '仪表盘'
})

// 用户下拉菜单选项
const userOptions = [
  { content: '个人设置', value: 'profile' },
  { content: '退出登录', value: 'logout' },
]

const handleMenuChange = (value: string) => {
  router.push(`/admin/${value}`)
}

const goHome = () => {
  router.push('/')
}

const goToChat = () => {
  router.push('/chat')
}

// 处理用户下拉菜单点击
const handleUserAction = async (data: { value: string }) => {
  console.log('Dropdown clicked:', data)
  const value = data.value

  if (value === 'logout') {
    console.log('Executing logout...')
    try {
      await authStore.logout()
      console.log('Logout success, redirecting...')
      router.push('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  } else if (value === 'profile') {
    MessagePlugin.info('个人设置功能开发中')
  }
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;

  :deep(.t-layout) {
    height: 100%;
  }

  :deep(.t-layout__content) {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
}

/* 侧边栏 */
.admin-sidebar {
  width: 240px;
  background: white;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e8e8e8;
  text-align: center;
}

.brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
  cursor: pointer;
  transition: opacity 0.3s;
}

.brand:hover {
  opacity: 0.8;
}

.brand-icon {
  font-size: 2rem;
}

.brand-subtitle {
  font-size: 0.875rem;
  color: #999;
  margin-top: 0.25rem;
}

.admin-menu {
  flex: 1;
  border-right: none;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid #e8e8e8;
}

/* 主内容区 */
.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

.admin-header {
  height: 60px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.username {
  margin-right: 4px;
}

.role-tag {
  margin-right: 4px;
}

.admin-content {
  flex: 1;
  padding: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.admin-content > * {
  flex: 1;
  min-height: 0;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
