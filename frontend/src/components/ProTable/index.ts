// 核心组件
export { default as ProTable } from './ProTable.vue'

// 类型定义
export type {
  ProTableData,
  ProTableValueType,
  ValueTypeConfig,
  SearchConfig,
  FormConfig,
  ProTableColumn,
  ToolbarConfig,
  OperationConfig,
  ProTableRequestParams,
  ProTableRequestResponse,
  ProTableConfig,
  ProTableEvents,
  ProTableExpose,
} from './types'

// 装饰器和高阶函数
export {
  // 装饰器
  Column,
  TableClass,
  getColumnsFromClass,

  // 链式 API
  ColumnBuilder,
  TableConfigBuilder,
  createColumn,
  createTableConfig,

  // 预设列类型
  textColumn,
  numberColumn,
  dateColumn,
  dateTimeColumn,
  tagColumn,
  selectColumn,
  switchColumn,
  imageColumn,
  linkColumn,
  operationColumn,

  // Composable
  useProTable,
} from './decorators'

// 渲染器工具
export {
  valueTypeRenderers,
  renderCell,
  renderSearchComponent,
  renderFormComponent,
  getFormRules,
  getFormDefaultValues,
} from './renderers'
