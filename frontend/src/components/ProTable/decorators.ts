import type { ProTableColumn, ProTableConfig, ProTableValueType, ValueTypeConfig, SearchConfig, FormConfig } from './types'
import type { VNode } from 'vue'

// 列配置元数据键
const COLUMN_METADATA_KEY = Symbol('protable:columns')


type SorterFn = (a: unknown, b: unknown) => number

// 列装饰器选项
interface ColumnDecoratorOptions {
  title?: string
  valueType?: ProTableValueType | ValueTypeConfig
  width?: number | string
  search?: boolean | SearchConfig
  form?: boolean | FormConfig
  hideInTable?: boolean
  hideInDescriptions?: boolean
  sorter?: boolean | SorterFn
  fixed?: 'left' | 'right'
  align?: 'left' | 'center' | 'right'
  ellipsis?: boolean
  copyable?: boolean
}

// 列装饰器 - 用于装饰类属性
export function Column(options: ColumnDecoratorOptions = {}) {

  return function (target: object, propertyKey: string) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const columns: ProTableColumn[] = (Reflect as any).getMetadata(COLUMN_METADATA_KEY, target) || []

    const column: ProTableColumn = {
      colKey: propertyKey,
      title: options.title || propertyKey,
      valueType: options.valueType,
      width: options.width,
      search: options.search,
      form: options.form,
      hideInTable: options.hideInTable,
      hideInDescriptions: options.hideInDescriptions,
      sorter: options.sorter,
      fixed: options.fixed,
      align: options.align,
      ellipsis: options.ellipsis,
      copyable: options.copyable,
    }

    columns.push(column)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(Reflect as any).defineMetadata(COLUMN_METADATA_KEY, columns, target)
  }
}

// 获取列配置

export function getColumnsFromClass(target: { new (...args: unknown[]): object }): ProTableColumn[] {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (Reflect as any).getMetadata(COLUMN_METADATA_KEY, target.prototype) || []
}

// 表格类装饰器选项
interface TableClassOptions {
  cardTitle?: string
  rowKey?: string
  pagination?: boolean
  search?: boolean
  index?: boolean | { title?: string; width?: number }
  selection?: boolean | 'single' | 'multiple'
  bordered?: boolean
  stripe?: boolean
  hover?: boolean
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor = new (...args: any[]) => object

// 表格类装饰器
export function TableClass(options: TableClassOptions = {}) {
  return function <T extends Constructor>(constructor: T) {
    const columns = getColumnsFromClass(constructor)

    return class extends constructor {
      static proTableConfig: Partial<ProTableConfig> = {
        columns,
        ...options,
      }

      getProTableConfig(): ProTableConfig {
        return {
          columns,
          ...options,
        } as ProTableConfig
      }
    }
  }
}

// ==================== 高阶函数 / 链式 API ====================

// 列构建器类 - 支持链式调用
export class ColumnBuilder {
  private column: ProTableColumn

  constructor(colKey: string, title: string) {
    this.column = {
      colKey,
      title,
    }
  }

  // 设置值类型
  valueType(type: ProTableValueType, config?: Omit<ValueTypeConfig, 'type'>) {
    this.column.valueType = config ? { type, ...config } : type
    return this
  }

  // 设置宽度
  width(width: number | string) {
    this.column.width = width
    return this
  }

  // 启用搜索
  search(config?: SearchConfig) {
    this.column.search = config ?? true
    return this
  }

  // 启用表单
  form(config?: FormConfig) {
    this.column.form = config ?? true
    return this
  }

  // 隐藏于表格
  hideInTable() {
    this.column.hideInTable = true
    return this
  }

  // 隐藏于详情
  hideInDescriptions() {
    this.column.hideInDescriptions = true
    return this
  }

  // 启用排序
  sorter(compareFn?: (a: unknown, b: unknown) => number) {
    this.column.sorter = compareFn ?? true
    return this
  }

  // 启用筛选
  filter(options: Array<{ label: string; value: unknown }>) {
    this.column.filter = { options }
    return this
  }

  // 固定列
  fixed(position: 'left' | 'right') {
    this.column.fixed = position
    return this
  }

  // 对齐方式
  align(align: 'left' | 'center' | 'right') {
    this.column.align = align
    return this
  }

  // 省略显示
  ellipsis() {
    this.column.ellipsis = true
    return this
  }

  // 可复制
  copyable() {
    this.column.copyable = true
    return this
  }

  // 自定义渲染

  render(fn: (value: unknown, record: unknown, index: number) => VNode | string | number) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    this.column.render = fn as any
    return this
  }

  // 自定义表头
  renderHeader(fn: () => VNode) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    this.column.renderHeader = fn as any
    return this
  }

  // 构建列配置
  build(): ProTableColumn {
    return { ...this.column }
  }
}

// 创建列的工厂函数
export function createColumn(colKey: string, title: string): ColumnBuilder {
  return new ColumnBuilder(colKey, title)
}

// ==================== 表格配置构建器 ====================

export class TableConfigBuilder {
  private config: Partial<ProTableConfig> = {
    columns: [],
  }

  // 添加列
  column(builder: ColumnBuilder): this
  column(colKey: string, title: string, fn?: (builder: ColumnBuilder) => ColumnBuilder): this
  column(
    arg1: ColumnBuilder | string,
    arg2?: string,
    fn?: (builder: ColumnBuilder) => ColumnBuilder
  ): this {
    if (arg1 instanceof ColumnBuilder) {
      this.config.columns!.push(arg1.build())
    } else if (typeof arg1 === 'string' && arg2) {
      let builder = new ColumnBuilder(arg1, arg2)
      if (fn) {
        builder = fn(builder)
      }
      this.config.columns!.push(builder.build())
    }
    return this
  }

  // 批量添加列
  columns(...builders: ColumnBuilder[]): this {
    builders.forEach(builder => {
      this.config.columns!.push(builder.build())
    })
    return this
  }

  // 设置数据请求
  request(requestFn: ProTableConfig['request']) {
    this.config.request = requestFn
    return this
  }

  // 设置静态数据
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data(data: any[]) {
    this.config.data = data
    return this
  }

  // 设置行键
  rowKey(key: string) {
    this.config.rowKey = key
    return this
  }

  // 设置卡片标题
  cardTitle(title: string) {
    this.config.cardTitle = title
    return this
  }

  // 启用搜索
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  search(config?: boolean | any) {
    this.config.search = config ?? true
    return this
  }

  // 启用分页
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  pagination(config?: boolean | any) {
    this.config.pagination = config ?? true
    return this
  }

  // 启用序号列
  index(config?: boolean | { title?: string; width?: number }) {
    this.config.index = config ?? true
    return this
  }

  // 启用选择
  selection(type: boolean | 'single' | 'multiple' = true) {
    this.config.selection = type
    return this
  }

  // 设置工具栏
  toolbar(config: ProTableConfig['toolbar']) {
    this.config.toolbar = config
    return this
  }

  // 设置操作列
  operation(config: ProTableConfig['operation']) {
    this.config.operation = config
    return this
  }

  // 设置斑马纹
  stripe(enable = true) {
    this.config.stripe = enable
    return this
  }

  // 设置悬停效果
  hover(enable = true) {
    this.config.hover = enable
    return this
  }

  // 设置边框
  bordered(enable = true) {
    this.config.bordered = enable
    return this
  }

  // 设置尺寸
  size(size: 'small' | 'medium' | 'large') {
    this.config.size = size
    return this
  }

  // 设置树形数据
  tree(config: ProTableConfig['tree']) {
    this.config.tree = config
    return this
  }

  // 设置拖拽排序
  dragSort(enable = true) {
    this.config.dragSort = enable
    return this
  }

  // 设置编辑配置
  editable(config: ProTableConfig['editable']) {
    this.config.editable = config
    return this
  }

  // 设置详情配置
  descriptions(config: ProTableConfig['descriptions']) {
    this.config.descriptions = config
    return this
  }

  // 构建配置
  build(): ProTableConfig {
    return this.config as ProTableConfig
  }
}

// 创建表格配置的工厂函数
export function createTableConfig(): TableConfigBuilder {
  return new TableConfigBuilder()
}

// ==================== 预设列类型 ====================

// 文本列
export const textColumn = (colKey: string, title: string, options?: { search?: boolean; form?: boolean }) => {
  const builder = createColumn(colKey, title).valueType('text')
  if (options?.search) builder.search()
  if (options?.form) builder.form()
  return builder
}

// 数字列
export const numberColumn = (colKey: string, title: string, options?: { search?: boolean; form?: boolean; sorter?: boolean }) => {
  const builder = createColumn(colKey, title).valueType('number')
  if (options?.search) builder.search({ component: 'number' })
  if (options?.form) builder.form({ component: 'number' })
  if (options?.sorter) builder.sorter()
  return builder
}

// 日期列
export const dateColumn = (colKey: string, title: string, format?: string) => {
  return createColumn(colKey, title)
    .valueType('date', { format })
    .search({ component: 'date-picker' })
}

// 日期时间列
export const dateTimeColumn = (colKey: string, title: string, format?: string) => {
  return createColumn(colKey, title)
    .valueType('datetime', { format })
}

// 标签列
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const tagColumn = (colKey: string, title: string, options: Array<{ label: string; value: any; color?: string }>) => {
  return createColumn(colKey, title)
    .valueType('tag', { options })
    .search({ component: 'select', options })
}

// 选择列
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const selectColumn = (colKey: string, title: string, options: Array<{ label: string; value: any }>) => {
  return createColumn(colKey, title)
    .valueType('select', { options })
    .search({ component: 'select', options })
    .form({ component: 'select', options })
}

// 开关列
export const switchColumn = (colKey: string, title: string) => {
  return createColumn(colKey, title)
    .valueType('switch')
    .form({ component: 'switch' })
    .align('center')
}

// 图片列
export const imageColumn = (colKey: string, title: string) => {
  return createColumn(colKey, title)
    .valueType('image')
    .align('center')
}

// 链接列
export const linkColumn = (colKey: string, title: string) => {
  return createColumn(colKey, title)
    .valueType('link')
}

// 操作列
export const operationColumn = (width?: number) => {
  return createColumn('operation', '操作')
    .valueType('operation')
    .fixed('right')
    .width(width || 200)
}

// ==================== 组合式函数 ====================

import { ref, computed } from 'vue'

// 使用 ProTable 的 composable
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useProTable<T = any>(_config: ProTableConfig) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tableRef = ref<any>(null)
  const loading = ref(false)
  const selectedRows = ref<T[]>([])

  // 刷新数据
  const refresh = async () => {
    await tableRef.value?.refresh()
  }

  // 重置搜索
  const reset = () => {
    tableRef.value?.reset()
  }

  // 获取选中行
  const getSelectedRows = () => {
    return tableRef.value?.getSelectedRows() || []
  }

  // 清空选中
  const clearSelection = () => {
    tableRef.value?.clearSelection()
  }

  // 展开所有
  const expandAll = () => {
    tableRef.value?.expandAll()
  }

  // 收起所有
  const collapseAll = () => {
    tableRef.value?.collapseAll()
  }

  return {
    tableRef,
    loading,
    selectedRows,
    refresh,
    reset,
    getSelectedRows,
    clearSelection,
    expandAll,
    collapseAll,
  }
}
