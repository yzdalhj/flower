import apiClient from './client'
import type {
  Account,
  AccountListResponse,
  AccountStats,
  LimitStatus,
  CreateAccountRequest,
  UpdateAccountRequest,
} from '@/types'

export const accountApi = {
  // 获取账号列表
  async getAccounts(): Promise<AccountListResponse> {
    const response = await apiClient.get('/accounts')
    return response.data
  },

  // 获取账号详情
  async getAccount(id: string): Promise<Account> {
    const response = await apiClient.get(`/accounts/${id}`)
    return response.data
  },

  // 创建账号
  async createAccount(data: CreateAccountRequest): Promise<Account> {
    const response = await apiClient.post('/accounts', data)
    return response.data
  },

  // 更新账号
  async updateAccount(id: string, data: UpdateAccountRequest): Promise<Account> {
    const response = await apiClient.put(`/accounts/${id}`, data)
    return response.data
  },

  // 删除账号
  async deleteAccount(id: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/accounts/${id}`)
    return response.data
  },

  // 启动账号
  async startAccount(id: string): Promise<Account> {
    const response = await apiClient.post(`/accounts/${id}/start`)
    return response.data
  },

  // 停止账号
  async stopAccount(id: string): Promise<Account> {
    const response = await apiClient.post(`/accounts/${id}/stop`)
    return response.data
  },

  // 获取账号统计
  async getAccountStats(id: string): Promise<AccountStats> {
    const response = await apiClient.get(`/accounts/${id}/stats`)
    return response.data
  },

  // 获取账号限制状态
  async getLimitStatus(id: string): Promise<LimitStatus> {
    const response = await apiClient.get(`/accounts/${id}/limits`)
    return response.data
  },

  // 获取所有账号限制状态
  async getAllLimitStatus(): Promise<LimitStatus[]> {
    const response = await apiClient.get('/accounts/limits/all')
    return response.data
  },

  // 重置账号每日统计
  async resetDailyStats(id: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/accounts/${id}/reset-stats`)
    return response.data
  },
}
