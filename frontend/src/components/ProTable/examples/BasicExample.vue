<template>
  <div class="example-page">
    <h2>基础用法 - 数据驱动配置</h2>
    <ProTable :config="basicConfig" />

    <h2>链式 API 配置</h2>
    <ProTable :config="chainConfig" />

    <h2>带操作列</h2>
    <ProTable
      ref="tableRef"
      :config="operationConfig"
      @create="handleCreate"
      @edit="handleEdit"
      @delete="handleDelete"
    />

    <h2>使用预设列类型</h2>
    <ProTable :config="presetConfig" />
  </div>
</template>

<script setup lang="ts">
import { ref, h } from 'vue'
import { MessagePlugin, Tag } from 'tdesign-vue-next'
import { ProTable, createTableConfig, createColumn, textColumn, numberColumn, tagColumn, dateColumn, useProTable } from '../index'
import type { ProTableConfig, ProTableData } from '../index'

const tableRef = ref()

// ==================== 示例1: 基础数据驱动配置 ====================
const basicConfig: ProTableConfig = {
  cardTitle: '用户列表',
  columns: [
    {
      colKey: 'id',
      title: 'ID',
      width: 80,
      valueType: 'number',
    },
    {
      colKey: 'name',
      title: '姓名',
      valueType: 'text',
      search: true,
      form: {
        component: 'input',
        rules: [{ required: true, message: '请输入姓名' }],
      },
    },
    {
      colKey: 'email',
      title: '邮箱',
      valueType: 'text',
      search: true,
      form: true,
    },
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
      search: {
        component: 'select',
        options: [
          { label: '启用', value: 'active' },
          { label: '禁用', value: 'inactive' },
          { label: '待审核', value: 'pending' },
        ],
      },
      form: {
        component: 'select',
        options: [
          { label: '启用', value: 'active' },
          { label: '禁用', value: 'inactive' },
          { label: '待审核', value: 'pending' },
        ],
      },
    },
    {
      colKey: 'createdAt',
      title: '创建时间',
      valueType: 'datetime',
      sorter: true,
    },
  ],
  data: [
    { id: 1, name: '张三', email: 'zhangsan@example.com', status: 'active', createdAt: '2024-01-15 10:30:00' },
    { id: 2, name: '李四', email: 'lisi@example.com', status: 'inactive', createdAt: '2024-01-14 14:20:00' },
    { id: 3, name: '王五', email: 'wangwu@example.com', status: 'pending', createdAt: '2024-01-13 09:15:00' },
    { id: 4, name: '赵六', email: 'zhaoliu@example.com', status: 'active', createdAt: '2024-01-12 16:45:00' },
  ],
  search: true,
  pagination: true,
  index: true,
  stripe: true,
  hover: true,
}

// ==================== 示例2: 链式 API 配置 ====================
const chainConfig = createTableConfig()
  .cardTitle('链式 API 配置示例')
  .search()
  .pagination()
  .index()
  .stripe()
  .hover()
  .column('id', 'ID', b => b.width(80).valueType('number'))
  .column('name', '姓名', b => b
    .valueType('text')
    .search()
    .form({ rules: [{ required: true, message: '请输入姓名' }] })
  )
  .column('age', '年龄', b => b
    .valueType('number')
    .search({ component: 'number' })
    .form({ component: 'number' })
    .sorter()
    .align('center')
  )
  .column('gender', '性别', b => b
    .valueType('tag', {
      options: [
        { label: '男', value: 'male', color: 'primary' },
        { label: '女', value: 'female', color: 'danger' },
      ],
    })
    .search({ component: 'select', options: [
      { label: '男', value: 'male' },
      { label: '女', value: 'female' },
    ]})
    .form({ component: 'select', options: [
      { label: '男', value: 'male' },
      { label: '女', value: 'female' },
    ]})
    .align('center')
  )
  .column('email', '邮箱', b => b
    .valueType('text')
    .search()
    .form()
    .ellipsis()
  )
  .column(createColumn('status', '状态')
    .valueType('tag', {
      options: [
        { label: '在职', value: 'active', color: 'success' },
        { label: '离职', value: 'inactive', color: 'default' },
        { label: '试用期', value: 'probation', color: 'warning' },
      ],
    })
    .search({ component: 'select', options: [
      { label: '在职', value: 'active' },
      { label: '离职', value: 'inactive' },
      { label: '试用期', value: 'probation' },
    ]})
    .align('center')
  )
  .data([
    { id: 1, name: '张三', age: 28, gender: 'male', email: 'zhangsan@example.com', status: 'active' },
    { id: 2, name: '李四', age: 32, gender: 'female', email: 'lisi@example.com', status: 'probation' },
    { id: 3, name: '王五', age: 25, gender: 'male', email: 'wangwu@example.com', status: 'active' },
    { id: 4, name: '赵六', age: 30, gender: 'female', email: 'zhaoliu@example.com', status: 'inactive' },
  ])
  .build()

// ==================== 示例3: 带操作列 ====================
const operationConfig: ProTableConfig = {
  cardTitle: '带操作列示例',
  columns: [
    { colKey: 'id', title: 'ID', width: 80 },
    { colKey: 'name', title: '名称', search: true, form: true },
    { colKey: 'description', title: '描述', valueType: 'text', ellipsis: true },
    {
      colKey: 'type',
      title: '类型',
      valueType: 'tag',
      search: { component: 'select', options: [
        { label: '类型A', value: 'A' },
        { label: '类型B', value: 'B' },
        { label: '类型C', value: 'C' },
      ]},
    },
    { colKey: 'createdAt', title: '创建时间', valueType: 'datetime' },
  ],
  data: [
    { id: 1, name: '项目一', description: '这是一个示例项目描述，可能会很长很长', type: 'A', createdAt: '2024-01-15 10:30:00' },
    { id: 2, name: '项目二', description: '另一个项目', type: 'B', createdAt: '2024-01-14 14:20:00' },
    { id: 3, name: '项目三', description: '第三个项目', type: 'C', createdAt: '2024-01-13 09:15:00' },
  ],
  search: true,
  pagination: true,
  index: true,
  toolbar: {
    create: { text: '新建项目', icon: 'add' },
    refresh: true,
    density: true,
    columnSetting: true,
    export: true,
  },
  operation: {
    edit: true,
    delete: true,
    view: true,
    actions: [
      {
        key: 'copy',
        text: '复制',
        icon: 'copy',
        theme: 'primary',
        variant: 'text',
        onClick: (row) => {
          MessagePlugin.success(`复制了: ${row.name}`)
        },
      },
      {
        key: 'publish',
        text: (row) => row.published ? '下架' : '发布',
        theme: (row) => row.published ? 'warning' : 'success',
        variant: 'text',
        onClick: (row) => {
          MessagePlugin.success(`${row.published ? '下架' : '发布'}: ${row.name}`)
        },
      },
    ],
  },
}

// ==================== 示例4: 使用预设列类型 ====================
const presetConfig = createTableConfig()
  .cardTitle('预设列类型示例')
  .search()
  .pagination()
  .index()
  .stripe()
  .columns(
    textColumn('name', '名称', { search: true, form: true }),
    numberColumn('price', '价格', { search: true, form: true, sorter: true }),
    numberColumn('stock', '库存', { form: true }),
    tagColumn('category', '分类', [
      { label: '电子产品', value: 'electronics', color: 'primary' },
      { label: '服装', value: 'clothing', color: 'success' },
      { label: '食品', value: 'food', color: 'warning' },
    ]),
    dateColumn('productionDate', '生产日期'),
    dateTimeColumn('createdAt', '创建时间'),
    switchColumn('isOnSale', '是否上架'),
    operationColumn(250)
  )
  .toolbar({
    create: true,
    refresh: true,
    density: true,
    columnSetting: true,
  })
  .operation({
    edit: true,
    delete: true,
    view: true,
  })
  .data([
    { id: 1, name: 'iPhone 15', price: 6999, stock: 100, category: 'electronics', productionDate: '2024-01-01', createdAt: '2024-01-15 10:30:00', isOnSale: true },
    { id: 2, name: 'T恤', price: 99, stock: 500, category: 'clothing', productionDate: '2024-02-01', createdAt: '2024-02-15 14:20:00', isOnSale: true },
    { id: 3, name: '巧克力', price: 29, stock: 200, category: 'food', productionDate: '2024-03-01', createdAt: '2024-03-15 09:15:00', isOnSale: false },
  ])
  .build()

// ==================== 事件处理 ====================
const handleCreate = () => {
  MessagePlugin.info('点击了创建按钮')
}

const handleEdit = (row: ProTableData) => {
  MessagePlugin.info(`编辑: ${row.name}`)
}

const handleDelete = (row: ProTableData) => {
  MessagePlugin.warning(`删除: ${row.name}`)
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
</style>
