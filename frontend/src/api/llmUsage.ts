import apiClient from './client'

export interface LLMUsageRecord {
  id: string
  user_id?: string
  conversation_id?: string
  provider: string
  model: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  estimated_cost: number
  request_type: string
  operation?: string
  status: string
  latency_ms?: number
  prompt_summary?: string
  response_summary?: string
  created_at: string
}

export interface LLMUsageStatistics {
  id: string
  stat_date: string
  provider: string
  model: string
  total_requests: number
  total_prompt_tokens: number
  total_completion_tokens: number
  total_tokens: number
  total_cost: number
  success_count: number
  error_count: number
  avg_latency_ms?: number
}

export interface UserUsageStats {
  user_id: string
  period: string
  total_requests: number
  total_prompt_tokens: number
  total_completion_tokens: number
  total_tokens: number
  total_cost: number
}

export interface ProviderStats {
  provider: string
  total_requests: number
  total_tokens: number
  total_cost: number
}

export interface OperationStats {
  operation: string
  total_requests: number
  total_tokens: number
  avg_latency_ms: number
}

export interface DashboardData {
  period_days: number
  user_summary: UserUsageStats
  provider_breakdown: ProviderStats[]
  operation_breakdown: OperationStats[]
  recent_records: LLMUsageRecord[]
}

export const llmUsageApi = {
  // 获取仪表盘数据
  async getDashboard(days: number = 7): Promise<DashboardData> {
    const response = await apiClient.get('/llm-usage/dashboard', { params: { days } })
    return response.data.data
  },

  // 获取每日统计
  async getDailyStatistics(days: number = 30, provider?: string): Promise<LLMUsageStatistics[]> {
    const response = await apiClient.get('/llm-usage/statistics/daily', {
      params: { days, provider }
    })
    return response.data.data
  },

  // 获取厂商统计
  async getProviderStatistics(days: number = 30): Promise<ProviderStats[]> {
    const response = await apiClient.get('/llm-usage/statistics/providers', {
      params: { days }
    })
    return response.data.data
  },

  // 获取操作统计
  async getOperationStatistics(days: number = 30): Promise<OperationStats[]> {
    const response = await apiClient.get('/llm-usage/statistics/operations', {
      params: { days }
    })
    return response.data.data
  },

  // 获取用户使用统计
  async getUserStatistics(days: number = 30): Promise<UserUsageStats> {
    const response = await apiClient.get('/llm-usage/statistics/user', {
      params: { days }
    })
    return response.data.data
  },

  // 获取使用记录
  async getRecords(limit: number = 100, provider?: string): Promise<LLMUsageRecord[]> {
    const response = await apiClient.get('/llm-usage/records', {
      params: { limit, provider }
    })
    return response.data.data
  },

  // 获取对话使用统计
  async getConversationUsage(conversationId: string): Promise<{
    conversation_id: string
    total_requests: number
    total_tokens: number
    total_cost: number
  }> {
    const response = await apiClient.get(`/llm-usage/conversations/${conversationId}`)
    return response.data.data
  }
}
