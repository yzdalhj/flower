<template>
  <div class="memories-view">
    <ProTable
      ref="proTableRef"
      :config="tableConfig"
      @create="handleCreate"
      @edit="handleEdit"
      @delete="handleDelete"
      @view="handleView"
      @submit="handleSubmit"
    />

    <!-- 查看详情对话框 -->
    <t-dialog
      v-model:visible="showDetailDialog"
      header="记忆详情"
      width="500px"
      :footer="false"
    >
      <div v-if="selectedMemory" class="memory-detail">
        <div class="detail-item">
          <div class="detail-label">类型</div>
          <t-tag :theme="getTypeTheme(selectedMemory.memory_type)" variant="light">
            {{ getTypeLabel(selectedMemory.memory_type) }}
          </t-tag>
        </div>
        <div class="detail-item">
          <div class="detail-label">重要性</div>
          <t-rate :value="selectedMemory.importance" :count="10" readonly />
        </div>
        <div class="detail-item">
          <div class="detail-label">内容</div>
          <div class="detail-content">{{ selectedMemory.content }}</div>
        </div>
        <div v-if="selectedMemory.summary" class="detail-item">
          <div class="detail-label">摘要</div>
          <div class="detail-summary">{{ selectedMemory.summary }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">访问次数</div>
          <div>{{ selectedMemory.access_count }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">创建时间</div>
          <div>{{ formatTime(selectedMemory.created_at) }}</div>
        </div>
      </div>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { MessagePlugin, DialogPlugin, Tag, Rate } from 'tdesign-vue-next'
import { ProTable } from '@/components/ProTable'
import { memoryApi } from '@/api/memory'
import type { Memory, CreateMemoryRequest } from '@/api/memory'
import type { ProTableConfig } from '@/components/ProTable/types'

const proTableRef = ref<InstanceType<typeof ProTable>>()
const showDetailDialog = ref(false)
const selectedMemory = ref<Memory | null>(null)

const memoryTypeOptions = [
  { label: '事件记忆', value: 'episodic' },
  { label: '语义记忆', value: 'semantic' },
  { label: '情感记忆', value: 'emotional' },
  { label: '偏好记忆', value: 'preference' },
]

const getTypeTheme = (type: string): 'primary' | 'success' | 'warning' | 'danger' | 'default' => {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'default'> = {
    episodic: 'primary',
    semantic: 'success',
    emotional: 'warning',
    preference: 'default',
  }
  return map[type] || 'default'
}

const getTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    episodic: '事件',
    semantic: '语义',
    emotional: '情感',
    preference: '偏好',
  }
  return map[type] || type
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString()
}

// 表格配置
const tableConfig = ref<ProTableConfig>({
  cardTitle: '记忆管理',
  rowKey: 'id',
  index: true,
  columns: [
    {
      colKey: 'user_id',
      title: '用户ID',
      hideInTable: true,
      form: {
        component: 'input',
        rules: [{ required: true, message: '请输入用户ID' }],
      },
    },
    {
      colKey: 'memory_type',
      title: '类型',
      width: 100,
      search: {
        component: 'select',
        options: memoryTypeOptions,
      },
      form: {
        component: 'select',
        options: memoryTypeOptions,
        rules: [{ required: true, message: '请选择记忆类型' }],
      },
      render: (value: string) => {
        return h(Tag, { theme: getTypeTheme(value), variant: 'light' }, () => getTypeLabel(value))
      },
    },
    {
      colKey: 'content',
      title: '内容',
      ellipsis: true,
      search: true,
      form: {
        span: 12,
        component: 'textarea',
        attrs: {
          autosize: { minRows: 5, maxRows: 10 },
        },
        rules: [{ required: true, message: '请输入记忆内容' }],
      },
    },
    {
      colKey: 'summary',
      title: '摘要',
      hideInTable: true,
      form: {
        component: 'input',
      },
    },
    {
      colKey: 'importance',
      title: '重要性',
      width: 200,
      form: {
        component: 'number',
      },
      render: (value: number) => {
        return h(Rate, { value, count: 10, readonly: true, size: 'small' })
      },
    },
    {
      colKey: 'access_count',
      title: '访问',
      width: 80,
    },
    {
      colKey: 'created_at',
      title: '创建时间',
      width: 180,
      render: (value: string) => formatTime(value),
    },
  ],
  toolbar: {
    create: true,
    refresh: true,
    density: true,
    columnSetting: true,
  },
  operation: {
    view: { text: '查看', onClick: () => {} },
    edit: true,
    delete: true,
    width: 200,
  },
  request: async (params) => {
    const response = await memoryApi.getMemories({
      keyword: params.filters?.content as string,
      memory_type: params.filters?.memory_type as string,
      limit: params.pageSize,
      offset: (params.current - 1) * params.pageSize,
    })
    return {
      data: response.items,
      total: response.total,
    }
  },
})

const handleCreate = () => {
  // 创建按钮点击
}

const handleEdit = (row: any) => {
  // 编辑按钮点击
}

const handleDelete = (row: any) => {
  const confirmDialog = DialogPlugin.confirm({
    header: '确认删除',
    body: '确定要删除这条记忆吗？',
    onConfirm: async () => {
      try {
        await memoryApi.deleteMemory(row.id)
        MessagePlugin.success('记忆已删除')
        proTableRef.value?.refresh()
        confirmDialog.destroy()
      } catch (error) {
        MessagePlugin.error('删除失败')
        console.error(error)
      }
    },
  })
}

const handleView = (row: any) => {
  selectedMemory.value = row
  showDetailDialog.value = true
}

const handleSubmit = async (data: any, isEdit: boolean) => {
  try {
    if (isEdit && selectedMemory.value) {
      await memoryApi.updateMemory(selectedMemory.value.id, data)
      MessagePlugin.success('记忆已更新')
    } else {
      await memoryApi.createMemory(data)
      MessagePlugin.success('记忆已创建')
    }
    proTableRef.value?.refresh()
  } catch (error) {
    MessagePlugin.error('保存失败')
    console.error(error)
  }
}

onMounted(() => {
  // 页面加载时刷新数据
  proTableRef.value?.refresh()
})
</script>

<style scoped>
.memories-view {
  height: 100%;
  padding: 16px;
}

.memory-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-label {
  font-weight: 600;
  color: var(--td-text-color-secondary);
  font-size: 12px;
}

.detail-content {
  background: var(--td-bg-color-container);
  padding: 12px;
  border-radius: 8px;
  line-height: 1.6;
}

.detail-summary {
  background: var(--td-bg-color-secondarycontainer);
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--td-text-color-secondary);
}
</style>
