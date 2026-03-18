<template>
  <div ref="proTableRef" class="pro-table">
    <!-- 搜索表单 -->
    <t-card v-if="showSearch" class="pro-table-search" :bordered="false">
      <div class="search-form-wrapper">
        <t-form
          ref="searchFormRef"
          :data="searchParams"
          layout="inline"
          class="search-form"
          @submit="handleSearch"
          @reset="handleReset"
        >
          <div class="search-fields">
            <t-form-item
              v-for="column in searchColumns"
              :key="column.colKey"
              :label="column.title"
              :name="getSearchField(column)"
            >
              <component
                :is="getSearchComponent(column)"
                v-model="searchParams[getSearchField(column)]"
                v-bind="getSearchProps(column)"
              />
            </t-form-item>
          </div>
          <div class="search-actions">
            <t-space>
              <t-button theme="primary" type="submit">查询</t-button>
              <t-button theme="default" type="reset">重置</t-button>
              <t-button
                v-if="searchColumns.length > 3"
                theme="default"
                variant="text"
                @click="searchCollapsed = !searchCollapsed"
              >
                {{ searchCollapsed ? '展开' : '收起' }}
                <t-icon :name="searchCollapsed ? 'chevron-down' : 'chevron-up'" />
              </t-button>
            </t-space>
          </div>
        </t-form>
      </div>
    </t-card>

    <!-- 表格卡片 -->
    <t-card :title="config.cardTitle" :bordered="config.bordered ?? false" class="pro-table-card">
      <!-- 工具栏 -->
      <template #actions>
        <t-space>
          <!-- 创建按钮 -->
          <t-button v-if="toolbarConfig.create" theme="primary" @click="handleCreate">
            <template #icon><t-icon :name="createBtnConfig.icon || 'add'" /></template>
            {{ createBtnConfig.text || '新建' }}
          </t-button>

          <!-- 批量操作 -->
          <template v-if="selectedRowKeys.length > 0 && toolbarConfig.batchActions">
            <t-button
              v-for="action in toolbarConfig.batchActions"
              :key="action.key"
              :theme="action.theme || 'default'"
              @click="action.onClick(selectedRows)"
            >
              <template v-if="action.icon" #icon>
                <t-icon :name="action.icon" />
              </template>
              {{ action.text }}
            </t-button>
          </template>

          <!-- 刷新按钮 -->
          <t-button v-if="toolbarConfig.refresh !== false" variant="outline" @click="refresh">
            <template #icon><t-icon name="refresh" /></template>
          </t-button>

          <!-- 密度选择 -->
          <t-dropdown
            v-if="toolbarConfig.density"
            :options="densityOptions"
            @click="handleDensityChange"
          >
            <t-button variant="outline">
              <template #icon><t-icon name="view-list" /></template>
            </t-button>
          </t-dropdown>

          <!-- 列设置 -->
          <t-popup v-if="toolbarConfig.columnSetting" trigger="click" placement="bottom-right">
            <t-button variant="outline">
              <template #icon><t-icon name="setting" /></template>
            </t-button>
            <template #content>
              <div class="column-setting-panel">
                <div class="column-setting-header">
                  <t-checkbox
                    :model-value="allColumnsVisible"
                    :indeterminate="someColumnsVisible"
                    @change="handleToggleAllColumns"
                  >
                    列展示
                  </t-checkbox>
                </div>
                <t-divider />
                <div class="column-setting-list">
                  <t-checkbox-group
                    v-model="visibleColumnKeys"
                    direction="vertical"
                    @change="handleColumnVisibilityChange"
                  >
                    <t-checkbox
                      v-for="col in columnSettingList"
                      :key="col.colKey"
                      :value="col.colKey"
                    >
                      {{ col.title }}
                    </t-checkbox>
                  </t-checkbox-group>
                </div>
              </div>
            </template>
          </t-popup>

          <!-- 导出按钮 -->
          <t-button v-if="toolbarConfig.export" variant="outline" @click="handleExport">
            <template #icon><t-icon name="download" /></template>
          </t-button>
        </t-space>
      </template>

      <!-- 表格 -->
      <div ref="tableWrapperRef" class="table-wrapper">
        <t-table
          ref="tableRef"
          :data="tableData"
          :columns="visibleColumns"
          :loading="loading"
          :row-key="config.rowKey || 'id'"
          :selected-row-keys="selectedRowKeys"
          :size="tableSize"
          :stripe="config.stripe"
          :hover="config.hover"
          :tree="config.tree"
          draggable="config.dragSort"
          :height="tableWrapperHeight"
          @select-change="handleSelectChange"
          @page-change="handlePageChange"
          @sort-change="handleSortChange"
          @filter-change="handleFilterChange"
          @row-click="handleRowClick"
          @row-dblclick="handleRowDbClick"
        >
          <!-- 序号列 -->
          <template v-if="config.index" #serial-number="{ rowIndex }">
            {{ (pagination.current - 1) * pagination.pageSize + rowIndex + 1 }}
          </template>

          <!-- 动态列插槽 - 数据单元格 -->
          <template v-for="column in dataColumns" :key="column.colKey" #[column.colKey]="slotProps">
            <slot :name="column.colKey" v-bind="slotProps">
              <component
                :is="renderCellComponent"
                :value="slotProps.row[column.colKey]"
                :record="slotProps.row"
                :index="slotProps.rowIndex"
                :column="column"
              />
            </slot>
          </template>

          <!-- 动态列插槽 - 表头单元格 -->
          <template
            v-for="column in dataColumns"
            :key="'header-' + column.colKey"
            #[`header:${column.colKey}`]="slotProps"
          >
            {{ column.title }}
          </template>

          <!-- 操作列 -->
          <template v-if="operationConfig" #operation="{ row }">
            <t-space>
              <t-button
                v-if="operationConfig.view"
                size="small"
                variant="text"
                theme="primary"
                @click="handleView(row)"
              >
                {{ viewBtnConfig.text || '查看' }}
              </t-button>
              <t-button
                v-if="operationConfig.edit"
                size="small"
                variant="text"
                theme="primary"
                @click="handleEdit(row)"
              >
                {{ editBtnConfig.text || '编辑' }}
              </t-button>
              <t-button
                v-for="action in customActions"
                :key="action.key"
                size="small"
                :variant="action.variant || 'text'"
                :theme="getActionTheme(action, row)"
                :disabled="isActionDisabled(action, row)"
                @click="action.onClick(row)"
              >
                {{ getActionText(action, row) }}
              </t-button>
              <t-button
                v-if="operationConfig.delete"
                size="small"
                variant="text"
                theme="danger"
                @click="handleDelete(row)"
              >
                {{ deleteBtnConfig.text || '删除' }}
              </t-button>
            </t-space>
          </template>
        </t-table>
      </div>

      <!-- 分页 -->
      <div v-if="showPagination" class="pro-table-pagination">
        <t-pagination
          v-model="pagination.current"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-size-options="[10, 20, 50, 100]"
          show-jumper
          show-sizer
          @change="handlePageChange"
        />
      </div>
    </t-card>

    <!-- 创建/编辑对话框 -->
    <t-dialog
      v-model:visible="formVisible"
      :header="formTitle"
      :width="config.formDialog?.width || '50%'"
      :top="config.formDialog?.top || '10vh'"
      :confirm-btn="{ content: '保存', loading: formSubmitting }"
      @confirm="handleFormSubmit"
      @close="handleFormClose"
    >
      <div class="form-dialog-content">
        <t-form ref="formRef" :data="formData" :rules="formRules" :label-width="100">
          <t-row :gutter="[16, 16]">
            <t-col
              v-for="column in formColumns"
              :key="column.colKey"
              :span="getFormSpan(column)"
            >
              <t-form-item
                :label="column.title"
                :name="column.colKey"
              >
                <component
                  :is="getFormComponent(column)"
                  v-model="formData[column.colKey]"
                  v-bind="getFormProps(column)"
                />
              </t-form-item>
            </t-col>
          </t-row>
        </t-form>
      </div>
    </t-dialog>

    <!-- 详情抽屉 -->
    <t-drawer v-model:visible="detailVisible" :header="detailTitle" size="600px">
      <t-descriptions v-if="currentRecord" :column="descriptionsConfig.column || 1" bordered>
        <t-descriptions-item
          v-for="column in descriptionColumns"
          :key="column.colKey"
          :label="column.title"
        >
          <component
            :is="renderCellComponent"
            :value="currentRecord[column.colKey]"
            :record="currentRecord"
            :index="0"
            :column="column"
          />
        </t-descriptions-item>
      </t-descriptions>
    </t-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, defineComponent } from 'vue'
import {
  Card as TCard,
  Form as TForm,
  FormItem as TFormItem,
  Button as TButton,
  Space as TSpace,
  Table as TTable,
  Pagination as TPagination,
  Dialog as TDialog,
  Drawer as TDrawer,
  Descriptions as TDescriptions,
  DescriptionsItem as TDescriptionsItem,
  Checkbox as TCheckbox,
  CheckboxGroup as TCheckboxGroup,
  Divider as TDivider,
  Dropdown as TDropdown,
  Popup as TPopup,
  Icon as TIcon,
  MessagePlugin,
} from 'tdesign-vue-next'
import type {
  ProTableConfig,
  ProTableColumn,
  ProTableData,
  ProTableRequestParams,
  ProTableExpose,
  ToolbarConfig,
  OperationConfig,
} from './types'
import { renderCell, getFormRules, getFormDefaultValues } from './renderers'

// Props 定义
const props = defineProps<{
  config: ProTableConfig
}>()

// Emits 定义
const emit = defineEmits<{
  (e: 'create'): void
  (e: 'edit', record: ProTableData): void
  (e: 'delete', record: ProTableData): void
  (e: 'view', record: ProTableData): void
  (e: 'submit', data: ProTableData, isEdit: boolean): void
  (e: 'selection-change', keys: (string | number)[], rows: ProTableData[]): void
  (e: 'page-change', current: number, pageSize: number): void
  (e: 'row-click', record: ProTableData, index: number): void
}>()

// Refs
const tableRef = ref<InstanceType<typeof TTable>>()
const searchFormRef = ref<InstanceType<typeof TForm>>()
const formRef = ref<InstanceType<typeof TForm>>()
const proTableRef = ref<HTMLElement>()
const tableWrapperRef = ref<HTMLElement>()

// 状态
const loading = ref(false)
const tableWrapperHeight = ref<number>(400)
const tableData = ref<ProTableData[]>([])
const selectedRowKeys = ref<(string | number)[]>([])
const selectedRows = ref<ProTableData[]>([])
const searchParams = ref<Record<string, unknown>>({})
const searchCollapsed = ref(true)
const tableSize = ref<'small' | 'medium' | 'large'>('medium')
const visibleColumnKeys = ref<string[]>([])
const formVisible = ref(false)
const formSubmitting = ref(false)
const formData = ref<Record<string, unknown>>({})
const currentRecord = ref<ProTableData | null>(null)
const detailVisible = ref(false)
const isEditing = ref(false)

// 分页
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
})

// 计算属性
const config = computed(() => props.config)

const toolbarConfig = computed<ToolbarConfig>(() => ({
  create: true,
  refresh: true,
  ...config.value.toolbar,
}))

const operationConfig = computed<OperationConfig | undefined>(() => config.value.operation)

const showSearch = computed(() => {
  if (typeof config.value.search === 'boolean') return config.value.search
  return config.value.search !== undefined
})

const showPagination = computed(() => {
  if (typeof config.value.pagination === 'boolean') return config.value.pagination
  return true
})

const searchColumns = computed(() => {
  const columns = config.value.columns.filter((col) => col.search)
  if (searchCollapsed.value && columns.length > 3) {
    return columns.slice(0, 3)
  }
  return columns
})

const formColumns = computed(() => {
  return config.value.columns.filter((col) => col.form)
})

const descriptionColumns = computed(() => {
  return config.value.columns.filter((col) => !col.hideInDescriptions)
})

const dataColumns = computed(() => {
  return config.value.columns.filter((col) => !col.hideInTable)
})

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const visibleColumns = computed<any[]>(() => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const cols: any[] = dataColumns.value
    .filter((col) => visibleColumnKeys.value.includes(col.colKey))
    .map((col) => {
      // 移除 render 函数，避免传递给 TDesign 表格
      const { render, ...rest } = col
      return rest
    })

  // 添加序号列
  if (config.value.index) {
    const indexCol =
      typeof config.value.index === 'boolean'
        ? { colKey: 'serial-number', title: '序号', width: 80 }
        : {
            colKey: 'serial-number',
            title: config.value.index.title || '序号',
            width: config.value.index.width || 80,
          }
    cols.unshift(indexCol)
  }

  // 添加选择列
  if (config.value.selection) {
    cols.unshift({
      colKey: 'row-select',
      type: 'multiple',
      width: 50,
    })
  }

  // 添加操作列
  if (operationConfig.value) {
    cols.push({
      colKey: 'operation',
      title: '操作',
      width: operationConfig.value.width || 200,
      fixed: 'right',
    })
  }

  return cols
})

const columnSettingList = computed(() => {
  return dataColumns.value.map((col) => ({
    colKey: col.colKey,
    title: col.title,
  }))
})

const allColumnsVisible = computed(() => {
  return visibleColumnKeys.value.length === columnSettingList.value.length
})

const someColumnsVisible = computed(() => {
  return (
    visibleColumnKeys.value.length > 0 &&
    visibleColumnKeys.value.length < columnSettingList.value.length
  )
})

const createBtnConfig = computed(() => {
  if (typeof toolbarConfig.value.create === 'boolean') return {}
  return toolbarConfig.value.create || {}
})

const editBtnConfig = computed(() => {
  if (typeof operationConfig.value?.edit === 'boolean') return {}
  return operationConfig.value?.edit || {}
})

const deleteBtnConfig = computed(() => {
  if (typeof operationConfig.value?.delete === 'boolean') return {}
  return operationConfig.value?.delete || {}
})

const viewBtnConfig = computed(() => {
  if (typeof operationConfig.value?.view === 'boolean') return {}
  return operationConfig.value?.view || {}
})

const customActions = computed(() => {
  return operationConfig.value?.actions || []
})

const formTitle = computed(() => {
  return isEditing.value ? '编辑' : '新建'
})

const detailTitle = computed(() => {
  return '详情'
})

const descriptionsConfig = computed(() => {
  return config.value.descriptions || {}
})

const formRules = computed(() => {
  return getFormRules(config.value.columns)
})

const densityOptions = [
  { content: '紧凑', value: 'small' },
  { content: '适中', value: 'medium' },
  { content: '宽松', value: 'large' },
]

// 渲染单元格组件
const renderCellComponent = defineComponent({
  props: ['value', 'record', 'index', 'column'],
  setup(props) {
    return () => renderCell(props.value, props.record, props.index, props.column)
  },
})

// 方法
const fetchData = async () => {
  if (!config.value.request) return

  loading.value = true
  try {
    const params: ProTableRequestParams = {
      current: pagination.value.current,
      pageSize: pagination.value.pageSize,
      filters: searchParams.value,
      sort: {},
    }

    const res = await config.value.request(params)
    tableData.value = res.data
    pagination.value.total = res.total
  } finally {
    loading.value = false
  }
}

const refresh = async () => {
  await fetchData()
}

const reset = () => {
  searchParams.value = {}
  pagination.value.current = 1
  fetchData()
}

const handleSearch = () => {
  pagination.value.current = 1
  fetchData()
}

const handleReset = () => {
  searchParams.value = {}
  handleSearch()
}

const handlePageChange = (pageInfo: { current: number; pageSize: number }) => {
  pagination.value.current = pageInfo.current
  pagination.value.pageSize = pageInfo.pageSize
  fetchData()
  emit('page-change', pageInfo.current, pageInfo.pageSize)
}

const handleSortChange = () => {
  fetchData()
}

const handleFilterChange = () => {
  fetchData()
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleSelectChange = (keys: (string | number)[], options: any) => {
  selectedRowKeys.value = keys

  const rows = options?.selectedRowData || []
  selectedRows.value = rows
  emit('selection-change', keys, rows)
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleRowClick = (context: any) => {
  emit('row-click', context.row, context.index)
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleRowDbClick = (context: any) => {
  emit('row-click', context.row, context.index)
}

const handleCreate = () => {
  isEditing.value = false
  formData.value = { ...getFormDefaultValues(config.value.columns) }
  formVisible.value = true
  emit('create')
}

const handleEdit = (row: ProTableData) => {
  isEditing.value = true
  currentRecord.value = row
  formData.value = { ...row }
  formVisible.value = true
  emit('edit', row)
}

const handleDelete = (row: ProTableData) => {
  emit('delete', row)
}

const handleView = (row: ProTableData) => {
  currentRecord.value = row
  // 只有在没有自定义 onClick 时才打开内置抽屉
  const viewConfig = operationConfig.value?.view
  const hasCustomOnClick = typeof viewConfig === 'object' && viewConfig?.onClick
  if (!hasCustomOnClick) {
    detailVisible.value = true
  }
  emit('view', row)
}

const handleFormSubmit = async () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const valid = await (formRef.value as any)?.validate()
  if (valid !== true) return

  formSubmitting.value = true
  try {
    emit('submit', formData.value, isEditing.value)
    formVisible.value = false
    await fetchData()
  } finally {
    formSubmitting.value = false
  }
}

const handleFormClose = () => {
  formData.value = {}
  currentRecord.value = null
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleDensityChange = (dropdownItem: any) => {
  tableSize.value = dropdownItem?.value as 'small' | 'medium' | 'large'
}

const handleColumnVisibilityChange = (value: (string | number | boolean)[]) => {
  visibleColumnKeys.value = value.filter((v): v is string => typeof v === 'string')
}

const handleToggleAllColumns = (checked: boolean) => {
  if (checked) {
    visibleColumnKeys.value = columnSettingList.value.map((col) => col.colKey)
  } else {
    visibleColumnKeys.value = []
  }
}

const handleExport = () => {
  // 导出逻辑
  MessagePlugin.success('导出成功')
}

const getSearchField = (column: ProTableColumn): string => {
  if (typeof column.search === 'object' && column.search.field) {
    return column.search.field
  }
  return column.colKey
}

const getSearchComponent = (column: ProTableColumn) => {
  const searchConfig = typeof column.search === 'boolean' ? {} : column.search
  const component = searchConfig?.component || 'input'

  const componentMap: Record<string, string> = {
    input: 't-input',
    select: 't-select',
    'date-picker': 't-date-picker',
    'date-range': 't-date-range-picker',
    number: 't-input-number',
  }

  return componentMap[component] || 't-input'
}

const getSearchProps = (column: ProTableColumn) => {
  const searchConfig = typeof column.search === 'boolean' ? {} : column.search
  const placeholder = searchConfig?.placeholder || `请输入${column.title}`

  const props: Record<string, unknown> = {
    placeholder,
    clearable: true,
  }

  if (searchConfig?.options) {
    props.options = searchConfig.options
  }

  return props
}

const getFormComponent = (column: ProTableColumn) => {
  const formConfig = typeof column.form === 'boolean' ? {} : column.form
  const component = formConfig?.component || 'input'

  const componentMap: Record<string, string> = {
    input: 't-input',
    textarea: 't-textarea',
    select: 't-select',
    radio: 't-radio-group',
    checkbox: 't-checkbox-group',
    switch: 't-switch',
    number: 't-input-number',
    'date-picker': 't-date-picker',
  }

  return componentMap[component] || 't-input'
}

const getFormProps = (column: ProTableColumn) => {
  const formConfig = typeof column.form === 'boolean' ? {} : column.form
  const placeholder = formConfig?.placeholder || `请输入${column.title}`

  const props: Record<string, unknown> = {
    placeholder,
    clearable: true,
  }

  if (formConfig?.options) {
    props.options = formConfig.options
  }

  return props
}

const isActionDisabled = (
  action: { disabled?: boolean | ((row: ProTableData) => boolean) },
  row: ProTableData,
): boolean => {
  if (typeof action.disabled === 'function') {
    return action.disabled(row)
  }
  return action.disabled || false
}

const getActionText = (
  action: { text: string | ((row: ProTableData) => string) },
  row: ProTableData,
): string => {
  if (typeof action.text === 'function') {
    return action.text(row)
  }
  return action.text
}

// 获取表单栅格宽度，默认12（半行）
const getFormSpan = (column: ProTableColumn): number => {
  if (column.form && typeof column.form === 'object' && column.form.span !== undefined) {
    return column.form.span
  }
  return 6 // 默认占半行
}

const getActionTheme = (
  action: {
    theme?:
      | 'primary'
      | 'success'
      | 'warning'
      | 'danger'
      | 'default'
      | ((record: ProTableData) => 'primary' | 'success' | 'warning' | 'danger' | 'default')
  },
  row: ProTableData,
): 'primary' | 'success' | 'warning' | 'danger' | 'default' => {
  if (typeof action.theme === 'function') {
    return action.theme(row)
  }
  return action.theme || 'default'
}

const getSelectedRows = () => selectedRows.value
const clearSelection = () => {
  selectedRowKeys.value = []
  selectedRows.value = []
}
const setSelectedRows = (keys: (string | number)[]) => {
  selectedRowKeys.value = keys
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const expandAll = () => (tableRef.value as any)?.expandAll()
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const collapseAll = () => (tableRef.value as any)?.foldAll()

// 计算表格容器高度
const calcTableHeight = () => {
  if (!tableWrapperRef.value || !proTableRef.value) return

  const cardBody = proTableRef.value.querySelector('.pro-table-card ') as HTMLElement
  if (!cardBody) return

  // 获取卡片主体可用高度（使用 getBoundingClientRect 更准确）
  const rect = cardBody.getBoundingClientRect()
  const availableHeight = rect.height

  // 减去分页高度（如果显示分页）
  const paginationEl = proTableRef.value.querySelector('.pro-table-pagination') as HTMLElement
  const paginationHeight = paginationEl ? paginationEl.getBoundingClientRect().height : 0

  // 减去一些边距和边框的额外空间
  const extraSpace = 102

  // 设置表格高度
  const finalHeight = Math.floor(availableHeight - paginationHeight - extraSpace)
  tableWrapperHeight.value = finalHeight > 100 ? finalHeight : 100
}

// 初始化
onMounted(() => {
  // 初始化可见列
  visibleColumnKeys.value = dataColumns.value.map((col) => col.colKey)

  // 如果有静态数据，直接使用
  if (config.value.data) {
    tableData.value = config.value.data
    pagination.value.total = config.value.data.length
  } else {
    fetchData()
  }

  // 使用 ResizeObserver 监听容器高度变化
  calcTableHeight()
  const resizeObserver = new ResizeObserver(() => {
    calcTableHeight()
  })

  if (proTableRef.value) {
    resizeObserver.observe(proTableRef.value)
  }

  // 清理函数
  return () => {
    resizeObserver.disconnect()
  }
})

// 监听数据变化
watch(
  () => config.value.data,
  (newData) => {
    if (newData) {
      tableData.value = newData
      pagination.value.total = newData.length
    }
  },
  { deep: true },
)

// 暴露方法
defineExpose<ProTableExpose>({
  refresh,
  reset,
  getSelectedRows,
  clearSelection,
  setSelectedRows,
  expandAll,
  collapseAll,
  startEdit: () => {
    // 实现编辑逻辑
  },
  endEdit: () => {
    // 实现退出编辑逻辑
  },
  getFormData: () => formData.value,
  setFormData: (data) => {
    formData.value = data
  },
  validate: async () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const valid = await (formRef.value as any)?.validate()
    return valid === true
  },
})
</script>

<style scoped>
.pro-table {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.pro-table > * + * {
  margin-top: 16px;
}

.pro-table-search {
  flex-shrink: 0;
  :deep(.t-card__body) {
    padding: 16px 24px;
  }

  .search-form-wrapper {
    width: 100%;
  }

  .search-form {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: nowrap;
    gap: 16px;
  }

  .search-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    flex: 1;
    min-width: 0;
  }

  .search-actions {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    height: 32px;
    margin-top: 4px;
  }
}

.pro-table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  :deep(.t-card__header) {
    flex-shrink: 0;
    border-bottom: 1px solid var(--td-border-level-1-color);
  }

  :deep(.t-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
    min-height: 0;
  }

  .table-wrapper {
    flex: 1;
    overflow: auto;
  }

  .column-setting-header {
    padding: 8px;
  }

  .column-setting-list {
    max-height: 300px;
    overflow-y: auto;
    padding: 8px;
  }
}

/* 修复表格内容溢出到操作栏的问题 */
:deep(.t-table__cell) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 固定列（操作栏）样式 */
:deep(.t-table__cell--fixed-right) {
  background-color: #fff !important;
  z-index: 20;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.08);
}

:deep(.t-table__cell--fixed-right:hover) {
  background-color: #f5f7fa !important;
}

/* 表头固定列 */
:deep(.t-table__header .t-table__cell--fixed-right) {
  background-color: #f5f7fa !important;
  z-index: 21;
}

:deep(.t-table--striped:not(.t-table--header-fixed) > .t-table__content > table > tbody > tr:nth-of-type(odd):not(.t-table__expanded-row)){
  background-color: transparent;
}

/* 表单对话框内容区域样式 */
:deep(.t-dialog__body) {
  max-height: calc(80vh - 120px);
  overflow: hidden;
  padding: 0;
}

.form-dialog-content {
  max-height: calc(80vh - 120px);
  padding: 24px;
}

/* 隐藏滚动条但保留滚动功能 */
.form-dialog-content::-webkit-scrollbar {
  width: 6px;
}

.form-dialog-content::-webkit-scrollbar-track {
  background: transparent;
}

.form-dialog-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.form-dialog-content::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

/* 表单栅格样式 */
:deep(.t-form .t-row) {
  margin: 0;
}

:deep(.t-form .t-col) {
  box-sizing: border-box;
}

/* 确保对话框居中 */
:deep(.t-dialog__wrap) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.t-dialog__position) {
  position: relative;
  top: auto;
  left: auto;
  transform: none;
  margin: 0;
}
</style>
