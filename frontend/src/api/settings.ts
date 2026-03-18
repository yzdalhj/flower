import apiClient from './client'
import type { ApiResponse } from '@/types'

// LLM 厂商配置
export interface LLMProvider {
  id: string
  name: string
  display_name: string
  base_url: string
  api_key: string
  default_model: string
  models: string[]
  timeout: number
  max_retries: number
  is_enabled: boolean
  is_default: boolean
  priority: number
  description?: string
}

export interface CreateLLMProviderRequest {
  name: string
  display_name: string
  base_url: string
  api_key: string
  default_model: string
  models?: string[]
  timeout?: number
  max_retries?: number
  is_enabled?: boolean
  is_default?: boolean
  priority?: number
  description?: string
}

export interface UpdateLLMProviderRequest {
  display_name?: string
  base_url?: string
  api_key?: string
  default_model?: string
  models?: string[]
  timeout?: number
  max_retries?: number
  is_enabled?: boolean
  is_default?: boolean
  priority?: number
  description?: string
}

// 系统设置
export interface SystemSettings {
  emotion_analysis_enabled: boolean
  memory_enabled: boolean
  proactive_enabled: boolean
  sticker_enabled: boolean
  daily_message_limit: number
  daily_cost_limit: number
  fallback_enabled: boolean
  deep_thinking_enabled: boolean
}

export type UpdateSystemSettingsRequest = Partial<SystemSettings>

export const settingsApi = {
  // ========== LLM 厂商配置 ==========

  // 获取所有厂商配置
  async getProviders(enabledOnly: boolean = false): Promise<LLMProvider[]> {
    const response = await apiClient.get('/settings/providers', {
      params: { enabled_only: enabledOnly }
    })
    return response.data
  },

  // 创建厂商配置
  async createProvider(data: CreateLLMProviderRequest): Promise<LLMProvider> {
    const response = await apiClient.post('/settings/providers', data)
    return response.data
  },

  // 更新厂商配置
  async updateProvider(id: string, data: UpdateLLMProviderRequest): Promise<LLMProvider> {
    const response = await apiClient.put(`/settings/providers/${id}`, data)
    return response.data
  },

  // 删除厂商配置
  async deleteProvider(id: string): Promise<ApiResponse<void>> {
    const response = await apiClient.delete(`/settings/providers/${id}`)
    return response.data
  },

  // 初始化默认厂商
  async initDefaultProviders(): Promise<LLMProvider[]> {
    const response = await apiClient.post('/settings/providers/init-defaults')
    return response.data
  },

  // ========== 系统设置 ==========

  // 获取系统设置
  async getSettings(): Promise<SystemSettings> {
    const response = await apiClient.get('/settings')
    return response.data
  },

  // 更新系统设置
  async updateSettings(data: UpdateSystemSettingsRequest): Promise<SystemSettings> {
    const response = await apiClient.put('/settings', data)
    return response.data
  },

  // 重置系统设置
  async resetSettings(): Promise<SystemSettings> {
    const response = await apiClient.post('/settings/reset')
    return response.data
  },
}
