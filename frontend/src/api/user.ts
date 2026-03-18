import apiClient from './client'
import type { PaginatedResponse } from '@/types'

export interface User {
  id: string
  account_id: string
  account_name?: string
  platform_user_id: string
  platform_type: string
  nickname?: string
  avatar_url?: string
  relationship_stage: string
  trust_score: number
  intimacy_score: number
  total_messages: number
  last_interaction_at?: string
  created_at: string
  updated_at: string
}

export interface UserProfile {
  id: string
  user_id: string
  age?: number
  gender?: string
  location?: string
  occupation?: string
  interests?: string[]
  birthday?: string
  emotional_state?: string
  preferred_topics?: string[]
  disliked_topics?: string[]
}

export interface UserDetail extends User {
  profile?: UserProfile
}

export interface AccountTreeItem {
  id: string
  name: string
  platform: string
  status: string
  user_count: number
}

export interface UserQueryParams {
  page?: number
  pageSize?: number
  account_id?: string
  platform_type?: string
  relationship_stage?: string
}

export const userApi = {
  // 获取用户列表
  async getUsers(params: UserQueryParams = {}): Promise<PaginatedResponse<User>> {
    const response = await apiClient.get('/users', { params })
    return {
      data: response.data.items || [],
      total: response.data.total || 0,
    }
  },

  // 获取用户详情
  async getUserDetail(id: string): Promise<UserDetail> {
    const response = await apiClient.get(`/users/${id}`)
    return response.data
  },

  // 更新用户
  async updateUser(id: string, data: Partial<User>): Promise<User> {
    const response = await apiClient.put(`/users/${id}`, data)
    return response.data
  },

  // 删除用户
  async deleteUser(id: string): Promise<void> {
    await apiClient.delete(`/users/${id}`)
  },

  // 更新用户画像
  async updateUserProfile(id: string, data: Partial<UserProfile>): Promise<UserProfile> {
    const response = await apiClient.put(`/users/${id}/profile`, data)
    return response.data
  },

  // 获取账号树
  async getAccountTree(): Promise<AccountTreeItem[]> {
    const response = await apiClient.get('/users/accounts/tree')
    return response.data
  },
}
