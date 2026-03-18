<template>
  <div class="example-page">
    <h2>远程数据请求</h2>
    <ProTable :config="remoteConfig" />

    <h2>批量操作</h2>
    <ProTable
      ref="batchTableRef"
      :config="batchConfig"
      @selection-change="handleSelectionChange"
    />

    <h2>自定义渲染 (JSX)</h2>
    <ProTable :config="customRenderConfig">
      <!-- 自定义列插槽 -->
      <template #avatar="{ row }">
        <t-avatar :image="row.avatar" :alt="row.name" size="medium" />
      </template>

      <template #progress="{ row }">
        <t-progress :percentage="row.progress" :color="getProgressColor(row.progress)" />
      </template>
    </ProTable>

    <h2>树形数据</h2>
    <ProTable :config="treeConfig" />

    <h2>使用 Composable</h2>
    <ProTable ref="composableTableRef" :config="composableConfig" />
    <t-space class="action-bar">
      <t-button @click="handleRefresh">刷新</t-button>
      <t-button @click="handleReset">重置搜索</t-button>
      <t-button @click="handleGetSelected">获取选中行</t-button>
      <t-button @click="handleClearSelection">清空选中</t-button>
    </t-space>
  </div>
</template>

<script setup lang="tsx">
import { ref, h } from 'vue'
import { MessagePlugin, Tag, Avatar, Progress, Button, Space } from 'tdesign-vue-next'
import { ProTable, createTableConfig, createColumn, useProTable } from '../index'
import type { ProTableConfig, ProTableData } from '../index'

// ==================== 示例1: 远程数据请求 ====================
const mockRequest = async (params: any) => {
  // 模拟 API 请求
  console.log('请求参数:', params)

  // 模拟延迟
  await new Promise(resolve => setTimeout(resolve, 500))

  // 模拟数据
  const mockData = Array.from({ length: 45 }, (_, i) => ({
    id: i + 1,
    name: `用户${i + 1}`,
    email: `user${i + 1}@example.com`,
    status: ['active', 'inactive', 'pending'][i % 3],
    role: ['admin', 'editor', 'viewer'][i % 3],
    createdAt: new Date(Date.now() - i * 86400000).toISOString(),
  }))

  // 模拟分页
  const start = (params.current - 1) * params.pageSize
  const end = start + params.pageSize

  return {
    data: mockData.slice(start, end),
    total: mockData.length,
    success: true,
  }
}

const remoteConfig: ProTableConfig = {
  cardTitle: '远程数据示例',
  columns: [
    { colKey: 'id', title: 'ID', width: 80 },
    { colKey: 'name', title: '姓名', search: true, form: true },
    { colKey: 'email', title: '邮箱', search: true, form: true },
    {
      colKey: 'status',
      title: '状态',
      valueType: {
        type: 'tag',
        options: [
          { label: '启用', value: 'active', color: 'success' },
          { label: '禁用', value: 'inactive', color: 'danger' },
          { label: '待审核', value: 'pending', color: 'warning' },
        ],
      },
      search: { component: 'select', options: [
        { label: '启用', value: 'active' },
        { label: '禁用', value: 'inactive' },
        { label: '待审核', value: 'pending' },
      ]},
    },
    {
      colKey: 'role',
      title: '角色',
      valueType: {
        type: 'tag',
        options: [
          { label: '管理员', value: 'admin', color: 'danger' },
          { label: '编辑', value: 'editor', color: 'primary' },
          { label: '访客', value: 'viewer', color: 'default' },
        ],
      },
    },
    { colKey: 'createdAt', title: '创建时间', valueType: 'datetime', sorter: true },
  ],
  request: mockRequest,
  search: true,
  pagination: true,
  index: true,
  stripe: true,
  hover: true,
  toolbar: {
    create: true,
    refresh: true,
    density: true,
    columnSetting: true,
  },
}

// ==================== 示例2: 批量操作 ====================
const batchTableRef = ref()

const batchConfig: ProTableConfig = {
  cardTitle: '批量操作示例',
  columns: [
    { colKey: 'id', title: 'ID', width: 80 },
    { colKey: 'name', title: '名称' },
    { colKey: 'category', title: '分类' },
    { colKey: 'price', title: '价格', valueType: 'number' },
    { colKey: 'stock', title: '库存', valueType: 'number' },
  ],
  data: [
    { id: 1, name: '商品A', category: '电子产品', price: 2999, stock: 100 },
    { id: 2, name: '商品B', category: '服装', price: 199, stock: 500 },
    { id: 3, name: '商品C', category: '食品', price: 59, stock: 200 },
    { id: 4, name: '商品D', category: '电子产品', price: 5999, stock: 50 },
    { id: 5, name: '商品E', category: '服装', price: 299, stock: 300 },
  ],
  selection: 'multiple',
  pagination: true,
  index: true,
  toolbar: {
    batchActions: [
      {
        key: 'batch-delete',
        text: '批量删除',
        icon: 'delete',
        theme: 'danger',
        onClick: (rows) => {
          MessagePlugin.warning(`批量删除 ${rows.length} 项`)
        },
      },
      {
        key: 'batch-export',
        text: '批量导出',
        icon: 'download',
        theme: 'primary',
        onClick: (rows) => {
          MessagePlugin.success(`导出 ${rows.length} 项`)
        },
      },
      {
        key: 'batch-enable',
        text: '批量启用',
        icon: 'check-circle',
        theme: 'success',
        onClick: (rows) => {
          MessagePlugin.success(`启用 ${rows.length} 项`)
        },
      },
    ],
  },
}

const handleSelectionChange = (keys: (string | number)[], rows: ProTableData[]) => {
  console.log('选中行:', keys, rows)
}

// ==================== 示例3: 自定义渲染 (JSX) ====================
const getProgressColor = (progress: number) => {
  if (progress >= 80) return '#00a870'
  if (progress >= 50) return '#0052d9'
  return '#e34d59'
}

const customRenderConfig = createTableConfig()
  .cardTitle('自定义渲染示例')
  .search()
  .pagination()
  .index()
  .columns(
    createColumn('id', 'ID').width(80),
    createColumn('name', '姓名').search().form(),
    createColumn('avatar', '头像')
      .render((value, record) => {
        return h(Avatar, {
          image: value,
          alt: record.name,
          size: 'medium',
        })
      }),
    createColumn('department', '部门').search().form(),
    createColumn('status', '状态')
      .valueType('tag', {
        options: [
          { label: '在职', value: 'active', color: 'success' },
          { label: '休假', value: 'vacation', color: 'warning' },
          { label: '离职', value: 'resigned', color: 'default' },
        ],
      }),
    createColumn('progress', '任务进度')
      .render((value) => {
        return h(Progress, {
          percentage: value,
          color: getProgressColor(value),
        })
      })
      .align('center')
      .width(200),
    createColumn('performance', '绩效')
      .render((value) => {
        const colors = ['#e34d59', '#ed7b2f', '#0052d9', '#00a870']
        const stars = '★'.repeat(value)
        return h('span', {
          style: {
            color: colors[value - 1] || '#0052d9',
            fontSize: '16px',
            letterSpacing: '2px',
          },
        }, stars)
      })
      .align('center'),
    createColumn('salary', '薪资')
      .render((value) => {
        return h('span', {
          style: {
            color: '#0052d9',
            fontWeight: 'bold',
          },
        }, `¥${value.toLocaleString()}`)
      })
      .align('right'),
  )
  .data([
    { id: 1, name: '张三', avatar: 'https://tdesign.gtimg.com/site/avatar.jpg', department: '技术部', status: 'active', progress: 85, performance: 4, salary: 25000 },
    { id: 2, name: '李四', avatar: 'https://tdesign.gtimg.com/site/avatar.jpg', department: '产品部', status: 'vacation', progress: 60, performance: 3, salary: 20000 },
    { id: 3, name: '王五', avatar: 'https://tdesign.gtimg.com/site/avatar.jpg', department: '设计部', status: 'active', progress: 95, performance: 5, salary: 22000 },
    { id: 4, name: '赵六', avatar: 'https://tdesign.gtimg.com/site/avatar.jpg', department: '技术部', status: 'resigned', progress: 30, performance: 2, salary: 18000 },
  ])
  .build()

// ==================== 示例4: 树形数据 ====================
const treeConfig: ProTableConfig = {
  cardTitle: '树形数据示例',
  columns: [
    { colKey: 'name', title: '部门名称', width: 200 },
    { colKey: 'manager', title: '负责人' },
    { colKey: 'memberCount', title: '成员数', valueType: 'number', align: 'center' },
    { colKey: 'budget', title: '预算', valueType: 'number', align: 'right' },
    { colKey: 'status', title: '状态', valueType: 'switch', align: 'center' },
  ],
  data: [
    {
      id: 1,
      name: '总公司',
      manager: '总经理',
      memberCount: 500,
      budget: 10000000,
      status: true,
      children: [
        {
          id: 11,
          name: '技术部',
          manager: '张三',
          memberCount: 150,
          budget: 3000000,
          status: true,
          children: [
            { id: 111, name: '前端组', manager: '李四', memberCount: 50, budget: 1000000, status: true },
            { id: 112, name: '后端组', manager: '王五', memberCount: 60, budget: 1200000, status: true },
            { id: 113, name: '测试组', manager: '赵六', memberCount: 40, budget: 800000, status: true },
          ],
        },
        {
          id: 12,
          name: '产品部',
          manager: '钱七',
          memberCount: 80,
          budget: 2000000,
          status: true,
        },
        {
          id: 13,
          name: '市场部',
          manager: '孙八',
          memberCount: 120,
          budget: 2500000,
          status: false,
        },
      ],
    },
  ],
  tree: {
    childrenKey: 'children',
    indent: 24,
    expandAll: true,
  },
  pagination: false,
}

// ==================== 示例5: 使用 Composable ====================
const composableTableRef = ref()

const { refresh, reset, getSelectedRows, clearSelection } = useProTable(composableTableRef)

const composableConfig: ProTableConfig = {
  cardTitle: 'Composable 示例',
  columns: [
    { colKey: 'id', title: 'ID', width: 80 },
    { colKey: 'name', title: '名称', search: true },
    { colKey: 'value', title: '数值', valueType: 'number' },
  ],
  data: [
    { id: 1, name: '项目A', value: 100 },
    { id: 2, name: '项目B', value: 200 },
    { id: 3, name: '项目C', value: 300 },
  ],
  search: true,
  selection: 'multiple',
  pagination: true,
  index: true,
}

const handleRefresh = async () => {
  await composableTableRef.value?.refresh()
  MessagePlugin.success('已刷新')
}

const handleReset = () => {
  composableTableRef.value?.reset()
  MessagePlugin.success('已重置')
}

const handleGetSelected = () => {
  const rows = composableTableRef.value?.getSelectedRows()
  MessagePlugin.info(`选中 ${rows?.length || 0} 行`)
  console.log('选中行:', rows)
}

const handleClearSelection = () => {
  composableTableRef.value?.clearSelection()
  MessagePlugin.success('已清空选中')
}
</script>

<style scoped>
.example-page {
  padding: 24px;
}

h2 {
  margin: 32px 0 16px;
  font-size: 18px;
  font-weight: 600;
  color: var(--td-text-color-primary);
}

h2:first-child {
  margin-top: 0;
}

.action-bar {
  margin-top: 16px;
}
</style>
