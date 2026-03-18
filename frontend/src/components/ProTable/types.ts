import type { VNode, Component } from 'vue'
import type { TableProps, TableCol, PaginationProps, FormProps, FormRule } from 'tdesign-vue-next'

// 基础类型
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type ProTableData = Record<string, any>

export type ProTableValueType =
  | 'text'
  | 'number'
  | 'date'
  | 'datetime'
  | 'time'
  | 'select'
  | 'tag'
  | 'switch'
  | 'image'
  | 'link'
  | 'operation'
  | 'custom'

// 值类型配置
export interface ValueTypeConfig {
  type: ProTableValueType
  // 日期/时间格式化
  format?: string
  // 选项配置（用于 select/tag）
  options?: Array<{ label: string; value: any; color?: string }>
  // 是否可编辑
  editable?: boolean
  // 自定义渲染函数
  render?: (value: any, record: ProTableData, index: number) => VNode | string | number
}

// 搜索配置
export interface SearchConfig {
  // 是否开启搜索
  enabled?: boolean
  // 搜索组件类型
  component?: 'input' | 'select' | 'date-picker' | 'date-range' | 'number'
  // 搜索字段名（默认为 colKey）
  field?: string
  // 占位符
  placeholder?: string
  // 选项（用于 select）
  options?: Array<{ label: string; value: any }>
  // 默认值
  defaultValue?: any
  // 透传组件原生属性（支持 TDesign 组件所有属性）
  attrs?: Record<string, any>
}

// 表单配置（用于编辑/创建）
export interface FormConfig {
  // 是否显示在表单
  show?: boolean
  // 表单组件类型
  component?: 'input' | 'textarea' | 'select' | 'radio' | 'checkbox' | 'switch' | 'number' | 'date-picker'
  // 表单校验规则
  rules?: FormRule[]
  // 选项（用于 select/radio/checkbox）
  options?: Array<{ label: string; value: any }>
  // 占位符
  placeholder?: string
  // 默认值
  defaultValue?: any
  // 自定义渲染
  render?: (value: any, onChange: (val: any) => void) => VNode
  // 栅格宽度（24栅格系统），默认12
  span?: number
  // 透传组件原生属性（支持 TDesign 组件所有属性）
  attrs?: Record<string, any>
}

// 列配置
export interface ProTableColumn {
  // 列唯一标识
  colKey: string
  // 列标题
  title: string | (() => VNode)
  // 值类型配置
  valueType?: ProTableValueType | ValueTypeConfig
  // 搜索配置
  search?: boolean | SearchConfig
  // 表单配置
  form?: boolean | FormConfig
  // 是否隐藏列
  hideInTable?: boolean
  // 是否仅在详情中显示
  hideInDescriptions?: boolean
  // 是否可排序
  sorter?: boolean | ((a: any, b: any) => number)
  // 是否可筛选
  filter?: boolean | { options: Array<{ label: string; value: any }> }
  // 自定义单元格渲染（优先级高于 valueType）
  render?: (value: any, record: ProTableData, index: number) => VNode | string | number
  // 自定义表头渲染
  renderHeader?: () => VNode
  // 编辑配置
  editable?: {
    // 是否可编辑
    enabled: boolean
    // 编辑组件类型
    component?: 'input' | 'number' | 'select' | 'date-picker'
    // 编辑校验规则
    rules?: FormRule[]
  }
  // 列宽
  width?: number | string
  // 最小宽度
  minWidth?: number | string
  // 对齐方式
  align?: 'left' | 'center' | 'right'
  // 固定列
  fixed?: 'left' | 'right'
  // 省略显示
  ellipsis?: boolean
  // 可复制
  copyable?: boolean
  // 列类型
  type?: 'single' | 'multiple'
}

// 工具栏配置
export interface ToolbarConfig {
  // 显示创建按钮
  create?: boolean | { text?: string; icon?: string }
  // 显示刷新按钮
  refresh?: boolean
  // 显示密度选择
  density?: boolean
  // 显示列设置
  columnSetting?: boolean
  // 显示导出按钮
  export?: boolean | { filename?: string; fileType?: 'csv' | 'excel' }
  // 批量操作
  batchActions?: Array<{
    key: string
    text: string
    icon?: string
    theme?: 'primary' | 'success' | 'warning' | 'danger'
    onClick: (selectedRows: ProTableData[]) => void
  }>
}

// 操作列配置
export interface OperationConfig {
  // 显示编辑按钮
  edit?: boolean | { text?: string; onClick?: (record: ProTableData) => void }
  // 显示删除按钮
  delete?: boolean | { text?: string; onClick?: (record: ProTableData) => void }
  // 显示查看按钮
  view?: boolean | { text?: string; onClick?: (record: ProTableData) => void }
  // 自定义操作按钮
  actions?: Array<{
    key: string
    text: string | ((record: ProTableData) => string)
    icon?: string
    theme?: 'primary' | 'success' | 'warning' | 'danger' | 'default' | ((record: ProTableData) => 'primary' | 'success' | 'warning' | 'danger' | 'default')
    variant?: 'base' | 'outline' | 'dashed' | 'text'
    size?: 'small' | 'medium' | 'large'
    disabled?: boolean | ((record: ProTableData) => boolean)
    visible?: boolean | ((record: ProTableData) => boolean)
    onClick: (record: ProTableData) => void
  }>
  // 操作列宽度
  width?: number | string
}

// 请求参数
export interface ProTableRequestParams {
  // 当前页
  current: number
  // 每页条数
  pageSize: number
  // 搜索参数
  filters: Record<string, any>
  // 排序参数
  sort: { field?: string; order?: 'asc' | 'desc' }
}

// 请求响应
export interface ProTableRequestResponse<T = ProTableData> {
  data: T[]
  total: number
  success?: boolean
}

// ProTable 配置
export interface ProTableConfig {
  // 列配置
  columns: ProTableColumn[]
  // 数据请求函数
  request?: (params: ProTableRequestParams) => Promise<ProTableRequestResponse>
  // 静态数据
  data?: ProTableData[]
  // 行键
  rowKey?: string
  // 工具栏配置
  toolbar?: ToolbarConfig
  // 操作列配置
  operation?: OperationConfig
  // 分页配置
  pagination?: boolean | PaginationProps
  // 搜索表单配置
  search?: boolean | FormProps
  // 是否显示序号列
  index?: boolean | { title?: string; width?: number }
  // 是否可选择
  selection?: boolean | 'single' | 'multiple'
  // 卡片标题
  cardTitle?: string
  // 是否显示边框
  bordered?: boolean
  // 是否斑马纹
  stripe?: boolean
  // 是否悬停效果
  hover?: boolean
  // 尺寸
  size?: 'small' | 'medium' | 'large'
  // 加载状态
  loading?: boolean
  // 是否可拖拽排序
  dragSort?: boolean
  // 树形数据配置
  tree?: {
    childrenKey?: string
    indent?: number
    expandAll?: boolean
  }
  // 编辑配置
  editable?: {
    // 编辑类型：单行编辑/多行编辑
    type: 'single' | 'multiple'
    // 保存回调
    onSave?: (record: ProTableData, index: number) => Promise<boolean>
  }
  // 详情配置
  descriptions?: {
    // 详情标题
    title?: string
    // 详情列数
    column?: number
    // 是否可编辑
    editable?: boolean
  }
  // 表单对话框配置
  formDialog?: {
    // 对话框宽度，默认 50%
    width?: string
    // 对话框顶部位置，默认 10vh
    top?: string
  }
}

// 事件定义
export interface ProTableEvents {
  // 行点击
  onRowClick?: (record: ProTableData, index: number) => void
  // 行双击
  onRowDbClick?: (record: ProTableData, index: number) => void
  // 选择变化
  onSelectionChange?: (selectedRowKeys: (string | number)[], selectedRows: ProTableData[]) => void
  // 分页变化
  onPageChange?: (current: number, pageSize: number) => void
  // 排序变化
  onSortChange?: (sort: { field?: string; order?: 'asc' | 'desc' }) => void
  // 筛选变化
  onFilterChange?: (filters: Record<string, any>) => void
  // 数据变化
  onDataChange?: (data: ProTableData[]) => void
}

// 暴露的方法
export interface ProTableExpose {
  // 刷新数据
  refresh: () => Promise<void>
  // 重置搜索
  reset: () => void
  // 获取选中行
  getSelectedRows: () => ProTableData[]
  // 清空选中
  clearSelection: () => void
  // 设置选中
  setSelectedRows: (keys: (string | number)[]) => void
  // 展开/收起所有
  expandAll: () => void
  collapseAll: () => void
  // 进入编辑模式
  startEdit: (rowKey?: string | number) => void
  // 退出编辑模式
  endEdit: (rowKey?: string | number, save?: boolean) => void
  // 获取表单数据
  getFormData: () => Record<string, any>
  // 设置表单数据
  setFormData: (data: Record<string, any>) => void
  // 校验表单
  validate: () => Promise<boolean>
}
