import apiClient from './client'
import type { DashboardStats, AccountListResponse } from '@/types'

interface DashboardTrendResponse {
  success: boolean
  data: {
    period_days: number
    user_summary: {
      total_tokens: number
      total_cost: number
    }
    daily: Array<{
      stat_date: string
      total_tokens: number
      total_cost: number
    }>
  }
}

export const dashboardApi = {
  // 获取仪表盘统计数据（账号统计）
  async getStats(): Promise<DashboardStats> {
    // 获取账号列表并计算统计数据
    const response = await apiClient.get('/accounts')
    const data: AccountListResponse = response.data

    const accounts = data.accounts || []
    const activeAccounts = accounts.filter(a => a.status === 'active')

    // 计算统计数据
    const stats: DashboardStats = {
      total_accounts: accounts.length,
      active_accounts: activeAccounts.length,
      total_messages: accounts.reduce((sum, a) => sum + (a.total_message_count || 0), 0),
      today_messages: accounts.reduce((sum, a) => sum + (a.today_message_count || 0), 0),
      total_cost: accounts.reduce((sum, a) => sum + (a.total_cost || 0), 0),
      today_cost: accounts.reduce((sum, a) => sum + (a.today_cost || 0), 0),
    }

    return stats
  },

  // 获取消息趋势（最近N天）从后台LLM使用统计
  async getMessageTrend(days: number = 7): Promise<{ date: string; count: number }[]> {
    const response = await apiClient.get<DashboardTrendResponse>(`/llm-usage/dashboard?days=${days}`)
    if (response.data?.success && response.data.data?.daily) {
      return response.data.data.daily.map(item => ({
        date: item.stat_date,
        count: item.total_tokens,
      }))
    }
    return []
  },

  // 获取成本趋势（最近N天）从后台LLM使用统计
  async getCostTrend(days: number = 7): Promise<{ date: string; cost: number }[]> {
    const response = await apiClient.get<DashboardTrendResponse>(`/llm-usage/dashboard?days=${days}`)
    if (response.data?.success && response.data.data?.daily) {
      return response.data.data.daily.map(item => ({
        date: item.stat_date,
        cost: item.total_cost,
      }))
    }
    return []
  },
}
