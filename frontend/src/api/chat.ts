import apiClient from './client'
import type { ChatRequest, ChatResponse, ChatHistoryResponse, Message } from '@/types'

export const chatApi = {
  // 发送消息
  async sendMessage(data: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post('/chat/send', data)
    return response.data
  },

  // 获取对话历史
  async getHistory(conversationId: string): Promise<ChatHistoryResponse> {
    const response = await apiClient.get(`/chat/history/${conversationId}`)
    return response.data
  },
}
