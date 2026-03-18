import apiClient from './client'

export interface LoginRequest {
  username: string
  password: string
}

export interface AdminUser {
  id: string
  username: string
  nickname?: string
  email?: string
  avatar_url?: string
  role: string
  is_active: boolean
  last_login_at?: string
  login_count: number
  created_at?: string
  updated_at?: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: AdminUser
}

export interface AdminUserInfo extends AdminUser {}

export const authApi = {
  /**
   * 管理员登录
   */
  login(data: LoginRequest): Promise<LoginResponse> {
    return apiClient.post('/auth/login', data).then(res => res.data)
  },

  /**
   * 获取当前管理员信息
   */
  getMe(): Promise<AdminUserInfo> {
    return apiClient.get('/auth/me').then(res => res.data)
  },

  /**
   * 管理员登出
   */
  logout(): Promise<{ message: string }> {
    return apiClient.post('/auth/logout').then(res => res.data)
  },

  /**
   * 刷新令牌
   */
  refreshToken(): Promise<{ access_token: string; token_type: string; expires_in: number }> {
    return apiClient.post('/auth/refresh').then(res => res.data)
  },

  /**
   * 修改密码
   */
  changePassword(oldPassword: string, newPassword: string): Promise<{ message: string }> {
    return apiClient.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    }).then(res => res.data)
  },

  /**
   * 获取管理员列表（仅超级管理员）
   */
  listAdmins(): Promise<{ data: AdminUser[]; total: number }> {
    return apiClient.get('/auth/admins').then(res => res.data)
  },

  /**
   * 创建管理员（仅超级管理员）
   */
  createAdmin(data: {
    username: string
    password: string
    nickname?: string
    email?: string
    role?: string
  }): Promise<{ message: string; id: string }> {
    return apiClient.post('/auth/admins', data).then(res => res.data)
  },
}
