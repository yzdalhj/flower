<template>
  <div class="conversations-view">
    <ProTable
      ref="proTableRef"
      :config="tableConfig"
      @view="handleView"
      @delete="handleDelete"
    />

    <!-- 对话详情对话框 -->
    <t-dialog
      v-model:visible="showDetailDialog"
      header="对话详情"
      width="70%"
      top="10vh"
      :footer="false"
    >
      <div class="conversation-detail" v-if="selectedConversation">
        <div class="detail-header">
          <t-descriptions :column="3" bordered size="small">
            <t-descriptions-item label="会话标题">{{ selectedConversation.title || `对话 ${selectedConversation.id.slice(-6)}` }}</t-descriptions-item>
            <t-descriptions-item label="用户昵称">{{ selectedConversation.user_nickname || '-' }}</t-descriptions-item>
            <t-descriptions-item label="状态">
              <t-tag :theme="getStatusTheme(selectedConversation.status)">
                {{ getStatusText(selectedConversation.status) }}
              </t-tag>
            </t-descriptions-item>
            <t-descriptions-item label="消息数">{{ selectedConversation.message_count }}</t-descriptions-item>
            <t-descriptions-item label="创建时间">{{ formatTime(selectedConversation.created_at) }}</t-descriptions-item>
            <t-descriptions-item label="最后消息">{{ selectedConversation.last_message_at ? formatTime(selectedConversation.last_message_at) : '-' }}</t-descriptions-item>
          </t-descriptions>
        </div>

        <div class="messages-section">
          <div class="messages-header">
            <h4>消息记录</h4>
            <t-space>
              <t-button theme="default" size="small" @click="refreshMessages">
                <template #icon><t-icon name="refresh" /></template>
                刷新
              </t-button>
            </t-space>
          </div>

          <div class="messages-list" ref="messagesContainer">
            <div
              v-for="message in selectedConversation.messages"
              :key="message.id"
              class="detail-message"
              :class="message.role"
            >
              <div class="message-header">
                <t-tag :theme="message.role === 'user' ? 'default' : 'primary'" size="small">
                  {{ message.role === 'user' ? '用户' : 'AI小花' }}
                </t-tag>
                <span class="message-time">{{ message.created_at ? formatTime(message.created_at) : '-' }}</span>
              </div>
              <div class="message-content">{{ message.content }}</div>
              <div v-if="message.tokens_used" class="message-meta">
                <t-tag size="small" variant="light">Tokens: {{ message.tokens_used }}</t-tag>
                <t-tag v-if="message.model_used" size="small" variant="light">{{ message.model_used }}</t-tag>
              </div>
            </div>

            <!-- 加载更多 -->
            <div v-if="hasMoreMessages" class="load-more">
              <t-button theme="default" variant="text" size="small" :loading="loadingMore" @click="loadMoreMessages">
                加载更多
              </t-button>
            </div>
          </div>
        </div>
      </div>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { MessagePlugin, DialogPlugin, Tag } from 'tdesign-vue-next'
import ProTable from '@/components/ProTable/ProTable.vue'
import { conversationApi } from '@/api'
import type { Conversation, ConversationDetail } from '@/types'
import type { ProTableConfig, ProTableData } from '@/components/ProTable/types'

const proTableRef = ref<InstanceType<typeof ProTable>>()
const showDetailDialog = ref(false)
const selectedConversation = ref<ConversationDetail | null>(null)
const messagesContainer = ref<HTMLElement>()
const loadingMore = ref(false)
const currentMessagePage = ref(1)
const totalMessages = ref(0)

// 表格配置
const tableConfig = computed<ProTableConfig>(() => ({
  cardTitle: '对话记录',
  rowKey: 'id',
  stripe: true,
  hover: true,
  pagination: true,
  search: true,
  toolbar: {
    create: false,
    refresh: true,
    density: true,
    columnSetting: true,
  },
  operation: {
    view: { text: '查看', onClick: () => {} },
    edit: false,
    delete: true,
    width: 120,
  },
  request: async (params: { current: number; pageSize: number; filters: Record<string, unknown> }) => {
    const response = await conversationApi.getConversations({
      page: params.current,
      pageSize: params.pageSize,
      account_id: (params.filters.account_id as string) || undefined,
      user_id: (params.filters.user_id as string) || undefined,
      status: (params.filters.status as string) || undefined,
    })
    return {
      data: response.data,
      total: response.total,
    }
  },
  columns: [
    {
      colKey: 'title',
      title: '会话标题',
      width: 200,
      ellipsis: true,
      render: (value: string | null, row: any) => {
        const title = value || `对话 ${row.id.slice(-6)}`
        return h('div', {
          style: {
            fontWeight: 500,
            color: '#333',
          }
        }, title)
      },
    },
    {
      colKey: 'last_message_preview',
      title: '最后消息',
      width: 250,
      ellipsis: true,
      render: (value: string | null) => {
        return value || '-'
      },
    },
    {
      colKey: 'user_nickname',
      title: '用户',
      width: 120,
      ellipsis: true,
    },
    {
      colKey: 'account_id',
      title: '账号',
      width: 150,
      ellipsis: true,
      search: {
        component: 'input',
        placeholder: '请输入账号ID',
      },
    },
    {
      colKey: 'status',
      title: '状态',
      width: 80,
      search: {
        component: 'select',
        placeholder: '请选择状态',
        options: [
          { label: '活跃', value: 'active' },
          { label: '暂停', value: 'paused' },
          { label: '已结束', value: 'ended' },
        ],
      },
      render: (value: string) => {
        const themeMap: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'default'> = {
          active: 'success',
          paused: 'warning',
          ended: 'default',
        }
        const textMap: Record<string, string> = {
          active: '活跃',
          paused: '暂停',
          ended: '已结束',
        }
        const theme = themeMap[value] || 'default'
        return h(Tag, {
          theme,
          size: 'small',
        }, () => textMap[value] || value)
      },
    },
    {
      colKey: 'message_count',
      title: '消息数',
      width: 80,
      align: 'center',
    },
    {
      colKey: 'last_message_at',
      title: '最后消息时间',
      width: 160,
      render: (value: string | null) => value ? formatTime(value) : '-',
    },
  ],
}))

// 是否有更多消息
const hasMoreMessages = computed(() => {
  if (!selectedConversation.value) return false
  return selectedConversation.value.messages.length < totalMessages.value
})

// 查看对话详情
const handleView = async (row: ProTableData) => {
  const conversationRow = row as unknown as Conversation
  try {
    const detail = await conversationApi.getConversationDetail(conversationRow.id)
    selectedConversation.value = detail
    currentMessagePage.value = 1
    totalMessages.value = detail.message_count
    showDetailDialog.value = true
  } catch (error) {
    MessagePlugin.error('获取对话详情失败')
    console.error(error)
  }
}

// 删除对话
const handleDelete = (row: ProTableData) => {
  const conversationRow = row as unknown as Conversation
  const title = conversationRow.title || `对话 ${conversationRow.id.slice(-6)}`
  const confirmDialog = DialogPlugin.confirm({
    header: '确认删除',
    body: `确定要删除会话 "${title}" 吗？此操作不可恢复。`,
    confirmBtn: {
      content: '删除',
      theme: 'danger',
    },
    onConfirm: async () => {
      try {
        await conversationApi.deleteConversation(conversationRow.id)
        MessagePlugin.success('删除成功')
        proTableRef.value?.refresh()
        confirmDialog.destroy()
      } catch (error) {
        MessagePlugin.error('删除失败')
        console.error(error)
      }
    },
  })
}

// 刷新消息
const refreshMessages = async () => {
  if (!selectedConversation.value) return
  try {
    currentMessagePage.value = 1
    const response = await conversationApi.getConversationMessages(
      selectedConversation.value.id,
      1,
      20,
    )
    selectedConversation.value.messages = response.messages
    totalMessages.value = response.total
  } catch (error) {
    MessagePlugin.error('刷新消息失败')
    console.error(error)
  }
}

// 加载更多消息
const loadMoreMessages = async () => {
  if (!selectedConversation.value || loadingMore.value) return
  loadingMore.value = true
  try {
    currentMessagePage.value += 1
    const response = await conversationApi.getConversationMessages(
      selectedConversation.value.id,
      currentMessagePage.value,
      20,
    )
    selectedConversation.value.messages.unshift(...response.messages)
  } catch (error) {
    MessagePlugin.error('加载消息失败')
    console.error(error)
  } finally {
    loadingMore.value = false
  }
}

// 获取状态主题
const getStatusTheme = (status: string): string => {
  const themeMap: Record<string, string> = {
    active: 'success',
    paused: 'warning',
    ended: 'default',
  }
  return themeMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    active: '活跃',
    paused: '暂停',
    ended: '已结束',
  }
  return textMap[status] || status
}

// 格式化时间
const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}
</script>

<style scoped>
.conversations-view {
  height: 100%;
  padding: 16px;
}

.conversation-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-header {
  margin-bottom: 16px;
}

.messages-section {
  border-top: 1px solid var(--td-border-level-1-color);
  padding-top: 16px;
}

.messages-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.messages-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 8px;
}

.detail-message {
  padding: 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e7e7e7;
}

.detail-message.assistant {
  background: #e7f3ff;
  border-color: #b3d9ff;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-time {
  font-size: 12px;
  color: #999;
}

.message-content {
  color: #333;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-meta {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.load-more {
  text-align: center;
  padding: 8px;
}
</style>
