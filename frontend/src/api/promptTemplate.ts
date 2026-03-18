import apiClient from './client'

export interface PromptSection {
  id: string
  name: string
  section_type: string
  title?: string
  content: string
  sort_order: number
  is_active: boolean
  template_id?: string
  created_at?: string
  updated_at?: string
}

export interface PromptTemplate {
  id: string
  name: string
  description?: string
  personality_id?: string
  is_default: boolean
  is_active: boolean
  version: number
  sections: PromptSection[]
  created_at?: string
  updated_at?: string
}

export interface PromptVariable {
  id: string
  name: string
  description: string
  var_type: string
  default_value?: string
  is_required: boolean
  example?: string
  created_at?: string
  updated_at?: string
}

export interface CreateTemplateRequest {
  name: string
  description?: string
  personality_id?: string
  is_default?: boolean
  sections?: {
    name: string
    section_type: string
    content: string
    title?: string
    sort_order?: number
    is_active?: boolean
  }[]
}

export interface UpdateTemplateRequest {
  name?: string
  description?: string
  is_default?: boolean
  is_active?: boolean
}

export interface CreateSectionRequest {
  name: string
  section_type: string
  content: string
  title?: string
  sort_order?: number
  is_active?: boolean
}

export interface UpdateSectionRequest {
  name?: string
  title?: string
  content?: string
  sort_order?: number
  is_active?: boolean
}

export interface CreateVariableRequest {
  name: string
  description: string
  var_type?: string
  default_value?: string
  is_required?: boolean
  example?: string
}

export interface UpdateVariableRequest {
  description?: string
  default_value?: string
  is_required?: boolean
  example?: string
}

export interface ReorderSectionsRequest {
  section_orders: { section_id: string; sort_order: number }[]
}

export interface BuildPromptRequest {
  variables: Record<string, string>
}

// Prompt模板API
export const promptTemplateApi = {
  // 模板管理
  getTemplates: (params?: { personality_id?: string; is_active?: boolean; skip?: number; limit?: number }) =>
    apiClient.get<PromptTemplate[]>('/admin/prompt-templates/templates', { params }),

  getTemplate: (templateId: string) =>
    apiClient.get<PromptTemplate>(`/admin/prompt-templates/templates/${templateId}`),

  createTemplate: (data: CreateTemplateRequest) =>
    apiClient.post<PromptTemplate>('/admin/prompt-templates/templates', data),

  updateTemplate: (templateId: string, data: UpdateTemplateRequest) =>
    apiClient.put<PromptTemplate>(`/admin/prompt-templates/templates/${templateId}`, data),

  deleteTemplate: (templateId: string) =>
    apiClient.delete(`/admin/prompt-templates/templates/${templateId}`),

  buildPrompt: (templateId: string, data: BuildPromptRequest) =>
    apiClient.post<{ prompt: string }>(`/admin/prompt-templates/templates/${templateId}/build`, data),

  // 区块管理
  addSection: (templateId: string, data: CreateSectionRequest) =>
    apiClient.post<PromptSection>(`/admin/prompt-templates/templates/${templateId}/sections`, data),

  updateSection: (sectionId: string, data: UpdateSectionRequest) =>
    apiClient.put<PromptSection>(`/admin/prompt-templates/sections/${sectionId}`, data),

  deleteSection: (sectionId: string) =>
    apiClient.delete(`/admin/prompt-templates/sections/${sectionId}`),

  reorderSections: (templateId: string, data: ReorderSectionsRequest) =>
    apiClient.post(`/admin/prompt-templates/templates/${templateId}/reorder`, data),

  // 变量管理
  getVariables: () =>
    apiClient.get<PromptVariable[]>('/admin/prompt-templates/variables'),

  getVariable: (variableId: string) =>
    apiClient.get<PromptVariable>(`/admin/prompt-templates/variables/${variableId}`),

  createVariable: (data: CreateVariableRequest) =>
    apiClient.post<PromptVariable>('/admin/prompt-templates/variables', data),

  updateVariable: (variableId: string, data: UpdateVariableRequest) =>
    apiClient.put<PromptVariable>(`/admin/prompt-templates/variables/${variableId}`, data),

  deleteVariable: (variableId: string) =>
    apiClient.delete(`/admin/prompt-templates/variables/${variableId}`),

  // 便捷接口
  getTemplateByPersonality: (personalityId: string) =>
    apiClient.get<PromptTemplate | null>(`/admin/prompt-templates/by-personality/${personalityId}`),

  buildPromptForPersonality: (personalityId: string, data: BuildPromptRequest) =>
    apiClient.post<{ prompt: string }>(`/admin/prompt-templates/by-personality/${personalityId}/build`, data),
}
