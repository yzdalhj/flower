<template>
  <div class="chat-page">
    <!-- 顶部导航 -->
    <header class="chat-header">
      <div class="header-brand" @click="goHome">
        <span class="brand-icon">🌸</span>
        <span class="brand-text">AI小花</span>
      </div>
      <div class="header-account" v-if="accountStore.accounts.length > 0">
        <t-select
          v-model="selectedAccountId"
          placeholder="选择账号"
          style="width: 200px"
          @change="onAccountChange"
        >
          <t-option
            v-for="account in accountStore.runningAccounts"
            :key="account.id"
            :label="account.name"
            :value="account.id"
          />
        </t-select>
      </div>
      <div class="header-actions">
        <t-button theme="default" variant="text" @click="goAdmin">
          <template #icon><t-icon name="setting" /></template>
          管理后台
        </t-button>
      </div>
    </header>

    <!-- 聊天主体 -->
    <div class="chat-container">
      <!-- 左侧会话列表 -->
      <aside class="chat-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <t-button theme="primary" block @click="createNewConversation">
            <template #icon><t-icon name="add" /></template>
            新建对话
          </t-button>
        </div>

        <div class="conversations-list">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            class="conversation-item"
            :class="{ active: conv.id === chatStore.currentConversationId }"
            @click="switchConversation(conv)"
          >
            <div class="conversation-icon">💬</div>
            <div class="conversation-info">
              <div class="conversation-title">{{ conv.title }}</div>
              <div class="conversation-preview" v-if="conv.last_message_preview">
                {{ conv.last_message_preview }}
              </div>
              <div class="conversation-meta">
                <span class="message-count">{{ conv.message_count }}条消息</span>
                <span class="conversation-time">{{
                  formatTime(conv.last_message_at || conv.created_at)
                }}</span>
              </div>
            </div>
            <t-button
              theme="danger"
              variant="text"
              size="small"
              class="delete-btn"
              @click.stop="deleteConversation(conv)"
            >
              <t-icon name="delete" />
            </t-button>
          </div>

          <div v-if="conversations.length === 0" class="empty-conversations">
            <t-empty description="暂无对话记录" />
          </div>
        </div>
      </aside>

      <!-- 侧边栏切换按钮 -->
      <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
        <t-icon :name="sidebarCollapsed ? 'chevron-right' : 'chevron-left'" />
      </div>

      <!-- 聊天区域 -->
      <main class="chat-main">
        <!-- 欢迎界面 -->
        <div v-if="chatStore.messages.length === 0" class="welcome-screen">
          <div class="welcome-content">
            <div class="welcome-avatar" v-motion-bounce>🌸</div>
            <h2 class="welcome-title">你好呀，我是AI小花</h2>
            <p class="welcome-subtitle">
              {{ welcomeMessage }}
            </p>
            <div class="quick-starts">
              <t-tag
                v-for="prompt in quickPrompts"
                :key="prompt"
                class="quick-tag"
                theme="primary"
                variant="light"
                size="large"
                @click="startWithPrompt(prompt)"
              >
                {{ prompt }}
              </t-tag>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="messages-container" ref="messagesContainer">
          <div
            v-for="(message, index) in processedMessages"
            :key="index"
            v-show="shouldShowMessage(message)"
            class="message-item"
            :class="[message.role, { 'split-message': shouldShowAsSplit(message, index) }]"
            v-motion-slide-bottom
            :delay="getSplitMessageDelay(message)"
          >
            <div class="message-avatar" v-if="!shouldShowAsSplit(message, index)">
              {{ message.role === 'user' ? '👤' : '🌸' }}
            </div>
            <div class="message-avatar placeholder" v-else></div>
            <div class="message-content">
              <div class="message-bubble">
                <div v-if="message.sticker_url" class="sticker-container">
                  <img
                    :src="message.sticker_url"
                    :alt="message.sticker_name"
                    class="sticker-image"
                    @error="handleImageError"
                  />
                </div>
                <div v-if="!message.sticker_url || message.content.trim()" class="message-text">
                  {{ message.content }}
                </div>
              </div>
              <div class="message-time" v-if="!shouldShowAsSplit(message, index)">
                {{ formatTime(message.created_at) }}
              </div>
            </div>
          </div>

          <!-- 加载中 -->
          <div v-if="chatStore.sending" class="message-item assistant" v-motion-fade>
            <div class="message-avatar">🌸</div>
            <div class="message-content">
              <div class="message-bubble typing">
                <t-loading size="small" text="小花正在思考..." />
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-wrapper">
            <t-textarea
              v-model="inputMessage"
              placeholder="输入消息..."
              :autosize="{ minRows: 1, maxRows: 4 }"
              @keydown.enter.prevent="handleSend"
              :disabled="!canSend"
            />
            <t-button
              theme="primary"
              shape="circle"
              :disabled="!inputMessage.trim() || chatStore.sending || !canSend"
              @click="sendMessage"
            >
              <t-icon name="send" />
            </t-button>
          </div>
          <div class="input-hint">
            <span v-if="!selectedAccountId" class="hint-warning">请先选择一个账号</span>
            <span v-else-if="chatStore.sending">小花正在思考中...</span>
            <span v-else>按 Enter 发送，Shift + Enter 换行</span>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore, useAccountStore } from '@/stores'
import { chatApi, conversationApi } from '@/api'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import type { Conversation } from '@/types'

const router = useRouter()
const chatStore = useChatStore()
const accountStore = useAccountStore()

const inputMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const selectedAccountId = ref<string>('')
const conversations = ref<Conversation[]>([])
const sidebarCollapsed = ref(false)

const welcomeMessage = computed(() => {
  if (accountStore.runningAccounts.length === 0) {
    return '当前没有运行中的账号，请先到管理后台创建并启动一个账号~'
  }
  if (!selectedAccountId.value) {
    return '请先选择一个账号开始聊天~'
  }
  return '有什么想和我聊的吗？无论是开心的事还是烦恼，我都在这里陪着你～'
})

const canSend = computed(() => {
  return selectedAccountId.value && !chatStore.sending
})

// 记录初始消息数量（页面加载时的消息数）
const initialMessageCount = ref(0)

// 新消息的拆分消息显示状态
const newSplitMessageVisibility = ref<Map<string, boolean>>(new Map())

// 将消息按换行拆分（仅AI消息）
const processedMessages = computed(() => {
  const result: Array<{
    role: string
    content: string
    created_at?: string
    isSplit?: boolean
    splitIndex?: number
    splitGroupId?: string
    isNew?: boolean
    sticker_url?: string
    sticker_name?: string
  }> = []

  chatStore.messages.forEach((message, msgIndex) => {
    // 判断是否是新消息（基于初始消息数量）
    const isNewMessage = msgIndex >= initialMessageCount.value
    if (message.sticker_url) {
      // 如果消息有表情包，先单独插入一条表情包消息
      const groupId = `split-${msgIndex}-${message.created_at || Date.now()}`
      result.push({
        ...message,
        role: message.role,
        content: '',
        created_at: message.created_at,
        isSplit: false,
        splitIndex: 0,
        splitGroupId: groupId,
        isNew: isNewMessage,
      })
    }
    if (message.role === 'assistant' && message.content.includes('\n')) {
      // AI消息包含换行，拆分为多条
      const parts = message.content.split('\n').filter((part) => part.trim())
      const groupId = `split-${msgIndex}-${message.created_at || Date.now()}`
      parts.forEach((part, index) => {
        result.push({
          ...message,
          role: message.role,
          content: part.trim(),
          sticker_url: '',
          sticker_name: '',
          created_at: message.created_at,
          isSplit: index > 0, // 标记为拆分后的消息（非第一条）
          splitIndex: index,
          splitGroupId: groupId,
          isNew: isNewMessage, // 标记是否为新消息
        })
      })
    } else {
      result.push({
        ...message,
        sticker_url: '',
        sticker_name: '',
        splitIndex: 0,
        splitGroupId: `normal-${msgIndex}`,
        isNew: isNewMessage,
      })
    }
  })

  return result
})

// 计算每条拆分消息的延迟时间（毫秒）
const getSplitMessageDelay = (message: any): number => {
  if (!message.isSplit || !message.isNew) return 0
  return message.splitIndex * 800 // 每条间隔800ms
}

// 检查消息是否应该显示
const shouldShowMessage = (message: any): boolean => {
  // 历史消息或非拆分消息直接显示
  if (!message.isNew || !message.isSplit) return true
  // 新消息的拆分消息需要检查是否已标记为可见
  return (
    newSplitMessageVisibility.value.get(`${message.splitGroupId}-${message.splitIndex}`) || false
  )
}

// 处理新消息的拆分消息延迟显示
const handleNewSplitMessage = (messageIndex: number) => {
  const message = chatStore.messages[messageIndex]
  if (message && message.role === 'assistant' && message.content.includes('\n')) {
    const parts = message.content.split('\n').filter((part: string) => part.trim())
    const groupId = `split-${messageIndex}-${message.created_at || Date.now()}`

    // 立即显示第一条
    newSplitMessageVisibility.value.set(`${groupId}-0`, true)

    // 延迟显示后续拆分消息
    parts.slice(1).forEach((_, idx) => {
      const index = idx + 1
      setTimeout(() => {
        newSplitMessageVisibility.value.set(`${groupId}-${index}`, true)
      }, index * 800)
    })
  }
}

// 监听新消息
watch(
  () => chatStore.messages.length,
  (newLength, oldLength) => {
    // 初始化时记录初始消息数量
    if (oldLength === undefined && newLength > 0) {
      initialMessageCount.value = newLength
      scrollToBottom()
      return
    }

    // 只处理真正的新消息（长度增加时）
    if (newLength > (oldLength || 0)) {
      // 只处理新增的最后一条消息
      const newMessageIndex = newLength - 1
      handleNewSplitMessage(newMessageIndex)

      // 计算最长延迟：最后一条拆分消息显示完成后滚动到底部
      const lastMessage = chatStore.messages[newMessageIndex]
      if (lastMessage && lastMessage.content.includes('\n')) {
        const parts = lastMessage.content.split('\n').filter((part) => part.trim())
        const maxDelay = parts.length * 800 + 100
        setTimeout(() => {
          scrollToBottom()
        }, maxDelay)
      } else {
        setTimeout(() => {
          scrollToBottom()
        }, 100)
      }
    }
  },
)

// 判断是否显示为拆分消息（连续相同角色的消息，除第一条外都隐藏头像）
const shouldShowAsSplit = (message: any, index: number) => {
  if (index === 0) return false
  const prevMessage = processedMessages.value[index - 1]
  return message.role === prevMessage?.role
}

const quickPrompts = [
  '今天心情不太好...',
  '我想分享一个开心的事',
  '给我讲个笑话吧',
  '最近有什么好玩的吗？',
]

onMounted(async () => {
  // 加载账号列表
  await accountStore.fetchAccounts()

  // 如果有运行中的账号，默认选择第一个
  if (accountStore.runningAccounts.length > 0) {
    selectedAccountId.value = accountStore.runningAccounts[0]?.id || ''
    chatStore.setCurrentAccount(selectedAccountId.value)
    await loadConversations()
  }
})

// 加载会话列表
const loadConversations = async () => {
  if (!selectedAccountId.value) return

  try {
    console.log('[DEBUG] 加载会话列表, account_id:', selectedAccountId.value)
    const response = await conversationApi.getConversations({
      account_id: selectedAccountId.value,
      page: 1,
      pageSize: 20,
    })
    console.log('[DEBUG] 会话列表响应:', response)
    conversations.value = response.data || []
    console.log('[DEBUG] 会话数量:', conversations.value.length)

    // 如果有会话，自动加载最新的
    if (conversations.value.length > 0 && !chatStore.currentConversationId) {
      const latest = conversations.value[0]
      chatStore.setConversationId(latest?.id || '')
      await chatStore.fetchHistory(latest?.id || '')
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

// 获取会话标题
const getConversationTitle = (conv: Conversation) => {
  // 如果有最后一条消息，显示消息预览
  // 否则显示默认标题
  return `对话 ${conv.id.slice(-6)}`
}

// 切换会话
const switchConversation = async (conv: Conversation) => {
  // 清空当前消息
  chatStore.messages = []
  // 设置新会话ID
  chatStore.setConversationId(conv.id)
  // 加载历史消息
  await chatStore.fetchHistory(conv.id)
  // 滚动到底部
  scrollToBottom()
}

// 创建新会话
const createNewConversation = () => {
  chatStore.startNewConversation()
  MessagePlugin.success('已创建新对话')
}

// 删除会话
const deleteConversation = (conv: Conversation) => {
  const confirmDialog = DialogPlugin.confirm({
    header: '确认删除',
    body: '确定要删除这个对话吗？删除后无法恢复。',
    onConfirm: async () => {
      try {
        // TODO: 调用删除API
        // await chatApi.deleteConversation(conv.id)

        // 从列表中移除
        conversations.value = conversations.value.filter((c) => c.id !== conv.id)

        // 如果删除的是当前会话，清空消息
        if (conv.id === chatStore.currentConversationId) {
          chatStore.startNewConversation()
        }

        MessagePlugin.success('对话已删除')
        confirmDialog.destroy()
      } catch (error) {
        MessagePlugin.error('删除失败')
        console.error(error)
      }
    },
  })
}

const goHome = () => {
  router.push('/')
}

const goAdmin = () => {
  router.push('/admin')
}

const onAccountChange = async (value: string) => {
  selectedAccountId.value = value
  chatStore.setCurrentAccount(value)

  // 重新加载该账号的会话列表
  await loadConversations()

  MessagePlugin.success(`已切换到账号: ${accountStore.accounts.find((a) => a.id === value)?.name}`)
}

const startWithPrompt = async (prompt: string) => {
  if (!selectedAccountId.value) {
    MessagePlugin.warning('请先选择一个账号')
    return
  }
  inputMessage.value = prompt
  await sendMessage()
}

const handleSend = (e: KeyboardEvent) => {
  if (e.shiftKey) return
  sendMessage()
}

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || chatStore.sending) return

  if (!selectedAccountId.value) {
    MessagePlugin.warning('请先选择一个账号')
    return
  }

  inputMessage.value = ''
  await chatStore.sendMessage(content)
  scrollToBottom()

  // 发送消息后刷新会话列表（可能会有新会话）
  await loadConversations()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatTime = (time: string | undefined) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const handleImageError = (event: Event) => {
  console.warn('[Sticker] 图片加载失败:', (event.target as HTMLImageElement).src)
}

const hasOnlySticker = (content: string): boolean => {
  const trimmed = content.trim()
  if (!trimmed) return true
  const emojiRegex = /^[\p{Emoji}\s]+$/u
  return emojiRegex.test(trimmed) && trimmed.length <= 4
}
</script>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 顶部导航 */
.chat-header {
  height: 60px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.header-brand:hover {
  transform: scale(1.05);
}

.brand-icon {
  font-size: 28px;
}

.brand-text {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-account {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 聊天主体 */
.chat-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧会话列表 */
.chat-sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.3s ease;
}

.chat-sidebar.collapsed {
  width: 0;
  overflow: hidden;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.conversation-item:hover {
  background: rgba(102, 126, 234, 0.1);
}

.conversation-item.active {
  background: rgba(102, 126, 234, 0.15);
}

.conversation-item:hover .delete-btn {
  opacity: 1;
}

.conversation-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-preview {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 4px;
}

.conversation-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  font-size: 11px;
  color: #999;
}

.message-count {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 2px 6px;
  border-radius: 10px;
}

.conversation-time {
  font-size: 11px;
  color: #999;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
  padding: 4px;
}

.empty-conversations {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 14px;
}

.sidebar-toggle {
  position: fixed;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 60px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 0 8px 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
  transition: left 0.3s ease;
}

.chat-sidebar:not(.collapsed) + .sidebar-toggle {
  left: 280px;
}

/* 聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 欢迎界面 */
.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.welcome-content {
  text-align: center;
  max-width: 500px;
}

.welcome-avatar {
  font-size: 80px;
  margin-bottom: 24px;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin-bottom: 16px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.welcome-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 32px;
  line-height: 1.6;
}

.quick-starts {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.quick-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.quick-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 消息列表 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message-item.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-item.assistant {
  align-self: flex-start;
}

.message-item.split-message {
  margin-top: 4px;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-avatar.placeholder {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  background: transparent;
  box-shadow: none;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  word-wrap: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.sticker-container .sticker-image {
  display: block;
}

.sticker-container:has(.message-text) {
  padding-bottom: 4px;
}

.message-item.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-item.assistant .message-bubble {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-bubble.typing {
  background: rgba(255, 255, 255, 0.9);
}

.message-text {
  line-height: 1.6;
  font-size: 15px;
}

.sticker-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sticker-image {
  max-width: 240px;
  max-height: 240px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
  display: block;
  background: transparent;
}

.sticker-image:hover {
  transform: scale(1.02);
}

.message-item.assistant .sticker-image {
  background: transparent;
}

.message-item.user .sticker-image {
  background: transparent;
}

.message-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  padding: 0 4px;
}

.message-item.user .message-time {
  text-align: right;
}

/* 输入区域 */
.input-area {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding: 16px 24px;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper :deep(.t-textarea) {
  flex: 1;
}

.input-wrapper :deep(.t-textarea__inner) {
  border-radius: 20px;
  padding: 12px 20px;
  resize: none;
  background: #f5f5f5;
  border: none;
}

.input-wrapper :deep(.t-textarea__inner:focus) {
  background: white;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.input-hint {
  text-align: center;
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

.hint-warning {
  color: #ff6b6b;
}
</style>
