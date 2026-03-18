import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi, type AdminUser } from '@/api/auth'
import { MessagePlugin } from 'tdesign-vue-next'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<AdminUser | null>(null)
  const loading = ref(false)

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')
  const isAdmin = computed(() => user.value?.role === 'super_admin' || user.value?.role === 'admin')
  const isViewer = computed(() => user.value?.role === 'viewer')
  const username = computed(() => user.value?.nickname || user.value?.username || '管理员')
  const avatarUrl = computed(() => user.value?.avatar_url)
  const userRole = computed(() => {
    const roleMap: Record<string, string> = {
      'super_admin': '超级管理员',
      'admin': '管理员',
      'viewer': '访客',
    }
    return roleMap[user.value?.role || ''] || '管理员'
  })

  // Actions
  /**
   * 设置 token
   */
  function setToken(newToken: string | null) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('access_token', newToken)
    } else {
      localStorage.removeItem('access_token')
    }
  }

  /**
   * 设置用户信息
   */
  function setUser(userInfo: AdminUser | null) {
    user.value = userInfo
  }

  /**
   * 登录
   */
  async function login(username: string, password: string) {
    loading.value = true
    try {
      const response = await authApi.login({ username, password })
      setToken(response.access_token)
      setUser(response.user)
      MessagePlugin.success('登录成功')
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || '登录失败'
      MessagePlugin.error(message)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取当前管理员信息
   */
  async function fetchUserInfo() {
    if (!token.value) return false

    try {
      const userInfo = await authApi.getMe()
      setUser(userInfo)
      return true
    } catch (error) {
      // Token 无效，清除登录状态
      logout()
      return false
    }
  }

  /**
   * 登出
   */
  async function logout() {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      // 忽略登出错误
    } finally {
      setToken(null)
      setUser(null)
      MessagePlugin.success('已退出登录')
    }
  }

  /**
   * 初始化认证状态
   * 在应用启动时调用
   */
  async function initAuth() {
    if (token.value) {
      await fetchUserInfo()
    }
  }

  /**
   * 刷新令牌
   */
  async function refreshToken() {
    try {
      const response = await authApi.refreshToken()
      setToken(response.access_token)
      return true
    } catch (error) {
      logout()
      return false
    }
  }

  /**
   * 检查是否有指定权限
   */
  function hasPermission(permission: string): boolean {
    if (!user.value) return false

    const permissionsMap: Record<string, string[]> = {
      'super_admin': ['*'],  // 所有权限
      'admin': [
        'account:read', 'account:write',
        'user:read', 'user:write',
        'conversation:read', 'conversation:write',
        'memory:read', 'memory:write',
        'settings:read', 'settings:write',
        'llm_usage:read',
      ],
      'viewer': [
        'account:read',
        'user:read',
        'conversation:read',
        'memory:read',
        'settings:read',
        'llm_usage:read',
      ],
    }

    const userPermissions = permissionsMap[user.value.role] || []
    return userPermissions.includes('*') || userPermissions.includes(permission)
  }

  return {
    // State
    token,
    user,
    loading,
    // Getters
    isLoggedIn,
    isSuperAdmin,
    isAdmin,
    isViewer,
    username,
    avatarUrl,
    userRole,
    // Actions
    login,
    logout,
    fetchUserInfo,
    initAuth,
    refreshToken,
    setToken,
    setUser,
    hasPermission,
  }
})
