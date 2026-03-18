import apiClient from './client'

export interface PersonalityConfig {
  id: string
  name: string
  description?: string
  avatar_url?: string
  is_active: boolean
  is_system: boolean
  usage_count: number
  big_five: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    neuroticism: number
  }
  traits: {
    expressiveness: number
    humor: number
    sarcasm: number
    verbosity: number
    empathy: number
    warmth: number
    emotional_stability: number
    assertiveness: number
    casualness: number
    formality: number
  }
  tags: string[]
  created_by?: string
  created_at?: string
  updated_at?: string
}

export interface PersonalityConfigSimple {
  id: string
  name: string
  description?: string
  is_active: boolean
}

export interface CreatePersonalityConfigRequest {
  name: string
  description?: string
  avatar_url?: string
  is_active?: boolean
  openness?: number
  conscientiousness?: number
  extraversion?: number
  agreeableness?: number
  neuroticism?: number
  expressiveness?: number
  humor?: number
  sarcasm?: number
  verbosity?: number
  empathy?: number
  warmth?: number
  emotional_stability?: number
  assertiveness?: number
  casualness?: number
  formality?: number
  tags?: string[]
}

export const personalityApi = {
  /**
   * 获取人格配置列表
   */
  getConfigs(is_active?: boolean): Promise<{ total: number; configs: PersonalityConfig[] }> {
    return apiClient.get('/personality-configs', { params: { is_active } }).then(res => res.data)
  },

  /**
   * 获取简化的人格配置列表（用于下拉菜单）
   */
  getSimpleConfigs(is_active: boolean = true): Promise<PersonalityConfigSimple[]> {
    return apiClient.get('/personality-configs/simple', { params: { is_active } }).then(res => res.data)
  },

  /**
   * 获取人格配置详情
   */
  getConfig(id: string): Promise<PersonalityConfig> {
    return apiClient.get(`/personality-configs/${id}`).then(res => res.data)
  },

  /**
   * 创建人格配置
   */
  createConfig(data: CreatePersonalityConfigRequest): Promise<PersonalityConfig> {
    return apiClient.post('/personality-configs', data).then(res => res.data)
  },

  /**
   * 更新人格配置
   */
  updateConfig(id: string, data: Partial<CreatePersonalityConfigRequest>): Promise<PersonalityConfig> {
    return apiClient.put(`/personality-configs/${id}`, data).then(res => res.data)
  },

  /**
   * 删除人格配置
   */
  deleteConfig(id: string): Promise<{ message: string }> {
    return apiClient.delete(`/personality-configs/${id}`).then(res => res.data)
  },

  /**
   * 应用人格配置到账号
   */
  applyConfig(id: string): Promise<{ message: string; personality_config: any }> {
    return apiClient.post(`/personality-configs/${id}/apply`).then(res => res.data)
  },
}
