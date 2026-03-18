<template>
  <div class="accounts-view">
    <ProTable
      ref="tableRef"
      :config="tableConfig"
      @create="handleCreate"
      @edit="handleEdit"
      @delete="handleDelete"
      @submit="handleSubmit"
    />

    <!-- 删除确认对话框 -->
    <t-dialog
      v-model:visible="showDeleteDialog"
      header="确认删除"
      theme="danger"
      @confirm="handleDeleteConfirm"
    >
      <p>确定要删除账号 "{{ deletingAccount?.name }}" 吗？此操作不可恢复。</p>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { MessagePlugin, Tag, Space } from 'tdesign-vue-next'
import { ProTable } from '@/components/ProTable'
import { useAccountStore } from '@/stores'
import { personalityApi } from '@/api/personality'
import type { Account } from '@/types'
import type { ProTableConfig } from '@/components/ProTable'
import type { PersonalityConfigSimple } from '@/api/personality'

const accountStore = useAccountStore()
const tableRef = ref()

// 人格配置选项
const personalityOptions = ref<{ label: string; value: string }[]>([])

// 加载人格配置列表
const loadPersonalityOptions = async () => {
  try {
    const configs = await personalityApi.getSimpleConfigs(true)
    personalityOptions.value = configs.map(config => ({
      label: config.name,
      value: config.id,
    }))
  } catch (error) {
    console.error('加载人格配置失败:', error)
  }
}

onMounted(() => {
  loadPersonalityOptions()
})

const showDeleteDialog = ref(false)
const deletingAccount = ref<Account | null>(null)

// 平台选项
const platformOptions = [
  { label: '微信', value: 'wechat' },
  { label: '企业微信', value: 'wecom' },
  { label: 'QQ', value: 'qq' },
  { label: 'Web', value: 'web' },
]

// 人格风格选项
const styleOptions = [
  { label: '可爱', value: 'cute' },
  { label: '温柔', value: 'gentle' },
  { label: '酷帅', value: 'cool' },
  { label: '活泼', value: 'energetic' },
]

// 状态选项
const statusOptions = [
  { label: '运行中', value: 'running', color: 'success' as const },
  { label: '已停止', value: 'stopped', color: 'default' as const },
  { label: '错误', value: 'error', color: 'danger' as const },
]

// 表格配置
const tableConfig: ProTableConfig = {
  cardTitle: '账号管理',
  columns: [
    {
      colKey: 'name',
      title: '名称',
      search: true,
      form: {
        component: 'input',
        span: 12,
        rules: [{ required: true, message: '请输入账号名称' }],
      },
    },
    {
      colKey: 'platform',
      title: '平台',
      valueType: {
        type: 'tag',
        options: [
          { label: '微信', value: 'wechat', color: 'success' },
          { label: '企业微信', value: 'wecom', color: 'primary' },
          { label: 'QQ', value: 'qq', color: 'warning' },
          { label: 'Web', value: 'web', color: 'default' },
        ],
      },
      search: {
        component: 'select',
        options: platformOptions,
      },
      form: {
        component: 'select',
        options: platformOptions,
        rules: [{ required: true, message: '请选择平台' }],
      },
    },
    {
      colKey: 'status',
      title: '状态',
      width: 100,
      valueType: {
        type: 'tag',
        options: statusOptions,
      },
      search: {
        component: 'select',
        options: statusOptions.map(o => ({ label: o.label, value: o.value })),
      },
    },
    {
      colKey: 'stats',
      title: '消息统计',
      render: (_, row) => {
        const account = row as Account
        return h(Space, { direction: 'vertical', size: 'small' }, () => [
          h('div', { style: { fontSize: '12px' } }, `今日: ${account?.today_message_count || 0}`),
          h('div', { style: { fontSize: '12px' } }, `累计: ${account?.total_message_count || 0}`),
        ])
      },
    },
    {
      colKey: 'cost',
      title: '成本',
      render: (_, row) => {
        const account = row as Account
        return h(Space, { direction: 'vertical', size: 'small' }, () => [
          h('div', { style: { fontSize: '12px' } }, `今日: ¥${(account?.today_cost || 0).toFixed(2)}`),
          h('div', { style: { fontSize: '12px' } }, `累计: ¥${(account?.total_cost || 0).toFixed(2)}`),
        ])
      },
    },
    {
      colKey: 'personality_config_id',
      title: '人格配置',
      hideInTable: true,
      form: {
        component: 'select',
        options: personalityOptions.value,
        defaultValue: '',
      },
    },
    {
      colKey: 'enable_text',
      title: '文本消息',
      hideInTable: true,
      form: {
        component: 'switch',
        defaultValue: true,
      },
    },
    {
      colKey: 'enable_emoji',
      title: '表情回复',
      hideInTable: true,
      form: {
        component: 'switch',
        defaultValue: true,
      },
    },
    {
      colKey: 'enable_voice',
      title: '语音消息',
      hideInTable: true,
      form: {
        component: 'switch',
        defaultValue: false,
      },
    },
    {
      colKey: 'enable_image',
      title: '图片消息',
      hideInTable: true,
      form: {
        component: 'switch',
        defaultValue: true,
      },
    },
    {
      colKey: 'enable_proactive',
      title: '主动行为',
      hideInTable: true,
      form: {
        component: 'switch',
        defaultValue: true,
      },
    },
    {
      colKey: 'enable_learning',
      title: '学习功能',
      hideInTable: true,
      form: {
        component: 'switch',
        defaultValue: true,
      },
    },
    {
      colKey: 'max_daily_messages',
      title: '每日消息上限',
      hideInTable: true,
      form: {
        component: 'number',
        defaultValue: 1000,
      },
    },
    {
      colKey: 'max_daily_cost',
      title: '每日成本上限',
      hideInTable: true,
      form: {
        component: 'number',
        defaultValue: 50,
      },
    },
  ],
  request: async (params) => {
    await accountStore.fetchAccounts()
    return {
      data: accountStore.accounts,
      total: accountStore.accounts.length,
      success: true,
    }
  },
  search: true,
  pagination: true,
  index: true,
  stripe: true,
  hover: true,
  toolbar: {
    create: { text: '创建账号', icon: 'add' },
    refresh: true,
    density: true,
    columnSetting: true,
  },
  formDialog: {
    top: '10vh',
  },
  operation: {
    edit: true,
    delete: true,
    width: 220,
    actions: [
      {
        key: 'toggle',
        text: (row) => {
          const account = row as Account
          return account?.status === 'running' ? '停止' : '启动'
        },
        theme: (row: any): 'danger' | 'primary' => {
          const account = row as Account
          return account?.status === 'running' ? 'danger' : 'primary'
        },
        variant: 'text',
        onClick: async (row) => {
          const account = row as Account
          if (account?.status === 'running') {
            await accountStore.stopAccount(account.id)
            MessagePlugin.success('账号已停止')
          } else {
            await accountStore.startAccount(account.id)
            MessagePlugin.success('账号已启动')
          }
          tableRef.value?.refresh()
        },
      },
    ],
  },
}

const handleCreate = () => {
  console.log('创建账号')
}

const handleEdit = (row: any) => {
  const account = row as Account
  console.log('编辑账号:', account)
}

const handleDelete = (row: any) => {
  const account = row as Account
  deletingAccount.value = account
  showDeleteDialog.value = true
}

const handleDeleteConfirm = async () => {
  if (!deletingAccount.value) return
  const success = await accountStore.deleteAccount(deletingAccount.value.id)
  if (success) {
    MessagePlugin.success('账号已删除')
    showDeleteDialog.value = false
    deletingAccount.value = null
    tableRef.value?.refresh()
  }
}

const handleSubmit = async (data: any, isEdit: boolean) => {
  // 如果有选择人格配置，获取人格配置详情
  let personalityConfig = {
    openness: 50,
    conscientiousness: 50,
    extraversion: 50,
    agreeableness: 50,
    neuroticism: 50,
  }

  if (data.personality_config_id) {
    try {
      const config = await personalityApi.getConfig(data.personality_config_id)
      personalityConfig = config.big_five
      // 应用人格配置（增加使用计数）
      await personalityApi.applyConfig(data.personality_config_id)
    } catch (error) {
      console.error('获取人格配置失败:', error)
    }
  }

  // 映射表单字段到后端字段
  const accountData = {
    name: data.name,
    platform: data.platform,
    platform_config: data.platform_config || {},
    personality_config: personalityConfig,
    max_daily_messages: data.max_daily_messages ?? 1000,
    max_daily_cost: data.max_daily_cost ?? 50,
    // 功能开关映射
    enable_text: data.enable_text ?? true,
    enable_emoji: data.enable_emoji ?? true,
    enable_voice: data.enable_voice ?? false,
    enable_image: data.enable_image ?? true,
    enable_proactive: data.proactive_enabled ?? data.enable_proactive ?? true,
    enable_learning: data.memory_enabled ?? data.enable_learning ?? true,
  }

  if (isEdit) {
    await accountStore.updateAccount(data.id, accountData)
    MessagePlugin.success('账号已更新')
  } else {
    await accountStore.createAccount(accountData)
    MessagePlugin.success('账号已创建')
  }
  tableRef.value?.refresh()
}
</script>

<style scoped>
.accounts-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  padding: 16px;
}
</style>
