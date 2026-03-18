import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi } from '@/api'
import type { Message, ChatRequest } from '@/types'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<Message[]>([])
  const currentConversationId = ref<string | null>(null)
  const loading = ref(false)
  const sending = ref(false)
  const currentAccountId = ref<string>('')
  const currentUserId = ref<string>('default_user')

  // Actions
  async function fetchHistory(conversationId: string) {
    loading.value = true
    try {
      const response = await chatApi.getHistory(conversationId)
      messages.value = response.messages || []
      currentConversationId.value = conversationId
    } catch (error) {
      console.error('获取对话历史失败:', error)
      messages.value = []
    } finally {
      loading.value = false
    }
  }

  async function sendMessage(content: string) {
    if (!currentAccountId.value) {
      console.error('未选择账号')
      return null
    }

    sending.value = true

    try {
      // 先添加用户消息到本地
      const userMessage: Message = {
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      }
      messages.value.push(userMessage)

      // 准备请求数据
      const requestData: ChatRequest = {
        user_id: currentUserId.value,
        account_id: currentAccountId.value,
        message: content,
        conversation_id: currentConversationId.value || undefined,
      }

      console.log('[DEBUG] Sending message with conversation_id:', requestData.conversation_id)

      // 发送请求
      const response = await chatApi.sendMessage(requestData)

      console.log('[DEBUG] Received response with conversation_id:', response.conversation_id)

      // 保存对话ID（如果是新对话）
      if (response.conversation_id) {
        currentConversationId.value = response.conversation_id
        console.log('[DEBUG] Updated currentConversationId:', currentConversationId.value)
      }

      // 重新加载完整对话历史来获取最新消息列表
      const conversationId = response.conversation_id || currentConversationId.value
      if (conversationId) {
        await fetchHistory(conversationId)
      }

      return response
    } catch (error) {
      console.error('发送消息失败:', error)
      // 添加错误消息
      const errorMessage: Message = {
        role: 'assistant',
        content: '抱歉，我遇到了一些问题，请稍后再试。',
        created_at: new Date().toISOString(),
      }
      messages.value.push(errorMessage)
      return null
    } finally {
      sending.value = false
    }
  }

  function setCurrentAccount(accountId: string) {
    currentAccountId.value = accountId
  }

  function setCurrentUser(userId: string) {
    currentUserId.value = userId
  }

  function setConversationId(conversationId: string | null) {
    currentConversationId.value = conversationId
  }

  function clearMessages() {
    messages.value = []
    currentConversationId.value = null
  }

  function startNewConversation() {
    messages.value = []
    currentConversationId.value = null
  }

  return {
    messages,
    currentConversationId,
    loading,
    sending,
    currentAccountId,
    currentUserId,
    fetchHistory,
    sendMessage,
    setCurrentAccount,
    setCurrentUser,
    setConversationId,
    clearMessages,
    startNewConversation,
  }
})
