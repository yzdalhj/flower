import apiClient from './client'
import type { Conversation, ConversationDetail, ApiResponse, PaginatedResponse } from '@/types'

export interface ConversationQueryParams {
  page?: number
  pageSize?: number
  account_id?: string
  user_id?: string
  status?: string
}

export const conversationApi = {
  // 获取对话列表
  async getConversations(params: ConversationQueryParams = {}): Promise<PaginatedResponse<Conversation>> {
    const response = await apiClient.get('/conversations', { params })
    return {
      data: response.data.items || [],
      total: response.data.total || 0,
    }
  },

  // 获取对话详情
  async getConversationDetail(id: string): Promise<ConversationDetail> {
    const response = await apiClient.get(`/conversations/${id}`)
    return response.data
  },

  // 删除对话
  async deleteConversation(id: string): Promise<ApiResponse<void>> {
    const response = await apiClient.delete(`/conversations/${id}`)
    return response.data
  },

  // 获取对话消息（分页）
  async getConversationMessages(
    id: string,
    page: number = 1,
    pageSize: number = 20,
  ): Promise<{ total: number; messages: Array<{ id: string; role: string; content: string; created_at: string }> }> {
    const response = await apiClient.get(`/conversations/${id}/messages`, {
      params: { page, page_size: pageSize },
    })
    return response.data
  },
}
