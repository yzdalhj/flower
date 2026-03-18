import type { FormRule } from 'tdesign-vue-next'
import type { Component, VNode } from 'vue'

// 表单字段类型
export type FieldType =
  | 'input'
  | 'password'
  | 'number'
  | 'switch'
  | 'select'
  | 'textarea'
  | 'radio'
  | 'custom'
  | 'component'

// 选择器选项
export interface SelectOption {
  label: string
  value: string | number | boolean
}

// 组件字段配置
export interface ComponentField {
  // 组件类型
  component: Component | string
  // 组件属性
  props?: Record<string, unknown>
  // 组件事件
  events?: Record<string, (value: unknown) => void>
  // 渲染函数
  render?: (value: unknown, onChange: (val: unknown) => void) => VNode
}

// 表单字段配置
export interface FormField {
  key: string
  label: string
  type: FieldType
  placeholder?: string
  help?: string
  defaultValue?: unknown
  disabled?: boolean
  clearable?: boolean
  group?: string

  // 栅格布局 - 支持 1-24 列
  span?: number

  // 输入框/文本域
  rows?: number

  // 数字输入
  min?: number
  max?: number
  step?: number

  // 选择器/单选框
  options?: SelectOption[]

  // 校验规则
  rules?: FormRule[]

  // 自定义组件配置
  component?: ComponentField
}

// 字段分组配置
export interface FieldGroup {
  key: string
  title: string
}

// 字段分组
export interface FormFieldGroup {
  key: string
  title: string
  fields: FormField[]
}

// 表单配置
export interface FormConfig {
  fields: FormField[]
  groups?: FieldGroup[]
  labelWidth?: number | string
  showActions?: boolean
  showReset?: boolean
  submitText?: string
  resetText?: string
}
