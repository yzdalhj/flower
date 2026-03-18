import apiClient from './client'
import type { ApiResponse, PaginationParams } from '@/types'

export interface Memory {
  id: string
  user_id: string
  memory_type: string
  content: string
  summary?: string
  importance: number
  access_count: number
  created_at: string
  updated_at: string
  meta_data?: Record<string, unknown>
}

export interface MemoryListResponse {
  total: number
  items: Memory[]
}

export interface CreateMemoryRequest {
  user_id: string
  memory_type: string
  content: string
  summary?: string
  importance?: number
  meta_data?: Record<string, unknown>
}

export interface UpdateMemoryRequest {
  content?: string
  summary?: string
  importance?: number
  memory_type?: string
  meta_data?: Record<string, unknown>
}

export interface MemoryStats {
  total: number
  by_type: Record<string, number>
  avg_importance: number
}

export const memoryApi = {
  // 获取记忆列表
  async getMemories(params?: {
    user_id?: string
    memory_type?: string
    keyword?: string
    limit?: number
    offset?: number
  }): Promise<MemoryListResponse> {
    const response = await apiClient.get('/memories', { params })
    return response.data
  },

  // 创建记忆
  async createMemory(data: CreateMemoryRequest): Promise<Memory> {
    const response = await apiClient.post('/memories', data)
    return response.data
  },

  // 获取单个记忆
  async getMemory(id: string): Promise<Memory> {
    const response = await apiClient.get(`/memories/${id}`)
    return response.data
  },

  // 更新记忆
  async updateMemory(id: string, data: UpdateMemoryRequest): Promise<Memory> {
    const response = await apiClient.put(`/memories/${id}`, data)
    return response.data
  },

  // 删除记忆
  async deleteMemory(id: string): Promise<ApiResponse<void>> {
    const response = await apiClient.delete(`/memories/${id}`)
    return response.data
  },

  // 获取重要记忆
  async getImportantMemories(
    userId: string,
    minImportance: number = 7,
    limit: number = 10
  ): Promise<Memory[]> {
    const response = await apiClient.get(`/memories/${userId}/important`, {
      params: { min_importance: minImportance, limit },
    })
    return response.data
  },

  // 获取记忆统计
  async getMemoryStats(userId?: string): Promise<MemoryStats> {
    const response = await apiClient.get('/memories/stats/overview', {
      params: { user_id: userId },
    })
    return response.data
  },
}
