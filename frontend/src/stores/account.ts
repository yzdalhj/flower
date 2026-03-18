import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { accountApi } from '@/api'
import type { Account, AccountStats, LimitStatus, CreateAccountRequest, UpdateAccountRequest } from '@/types'

export const useAccountStore = defineStore('account', () => {
  // State
  const accounts = ref<Account[]>([])
  const currentAccount = ref<Account | null>(null)
  const accountStats = ref<Record<string, AccountStats>>({})
  const accountLimits = ref<Record<string, LimitStatus>>({})
  const loading = ref(false)
  const total = ref(0)

  // Getters
  const runningAccounts = computed(() => accounts.value.filter((a) => a.status === 'running'))
  const stoppedAccounts = computed(() => accounts.value.filter((a) => a.status === 'stopped'))
  const errorAccounts = computed(() => accounts.value.filter((a) => a.status === 'error'))

  // Actions
  async function fetchAccounts() {
    loading.value = true
    try {
      const response = await accountApi.getAccounts()
      accounts.value = response.accounts || []
      total.value = response.total || 0
    } catch (error) {
      console.error('获取账号列表失败:', error)
      accounts.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  async function fetchAccount(id: string) {
    try {
      const account = await accountApi.getAccount(id)
      currentAccount.value = account
      return account
    } catch (error) {
      console.error('获取账号详情失败:', error)
      return null
    }
  }

  async function createAccount(data: CreateAccountRequest) {
    try {
      const account = await accountApi.createAccount(data)
      accounts.value.push(account)
      total.value++
      return account
    } catch (error) {
      console.error('创建账号失败:', error)
      return null
    }
  }

  async function updateAccount(id: string, data: UpdateAccountRequest) {
    try {
      const account = await accountApi.updateAccount(id, data)
      const index = accounts.value.findIndex((a) => a.id === id)
      if (index !== -1) {
        accounts.value[index] = account
      }
      if (currentAccount.value?.id === id) {
        currentAccount.value = account
      }
      return account
    } catch (error) {
      console.error('更新账号失败:', error)
      return null
    }
  }

  async function deleteAccount(id: string) {
    try {
      await accountApi.deleteAccount(id)
      accounts.value = accounts.value.filter((a) => a.id !== id)
      if (currentAccount.value?.id === id) {
        currentAccount.value = null
      }
      total.value--
      return true
    } catch (error) {
      console.error('删除账号失败:', error)
      return false
    }
  }

  async function startAccount(id: string) {
    try {
      const account = await accountApi.startAccount(id)
      const index = accounts.value.findIndex((a) => a.id === id)
      if (index !== -1) {
        accounts.value[index] = account
      }
      return account
    } catch (error) {
      console.error('启动账号失败:', error)
      return null
    }
  }

  async function stopAccount(id: string) {
    try {
      const account = await accountApi.stopAccount(id)
      const index = accounts.value.findIndex((a) => a.id === id)
      if (index !== -1) {
        accounts.value[index] = account
      }
      return account
    } catch (error) {
      console.error('停止账号失败:', error)
      return null
    }
  }

  async function fetchAccountStats(id: string) {
    try {
      const stats = await accountApi.getAccountStats(id)
      accountStats.value[id] = stats
      return stats
    } catch (error) {
      console.error('获取账号统计失败:', error)
      return null
    }
  }

  async function fetchAccountLimits(id: string) {
    try {
      const limits = await accountApi.getLimitStatus(id)
      accountLimits.value[id] = limits
      return limits
    } catch (error) {
      console.error('获取账号限制失败:', error)
      return null
    }
  }

  function setCurrentAccount(account: Account | null) {
    currentAccount.value = account
  }

  return {
    accounts,
    currentAccount,
    accountStats,
    accountLimits,
    loading,
    total,
    runningAccounts,
    stoppedAccounts,
    errorAccounts,
    fetchAccounts,
    fetchAccount,
    createAccount,
    updateAccount,
    deleteAccount,
    startAccount,
    stopAccount,
    fetchAccountStats,
    fetchAccountLimits,
    setCurrentAccount,
  }
})
