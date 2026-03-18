import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dashboardApi } from '@/api'
import type { DashboardStats } from '@/types'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const stats = ref<DashboardStats>({
    total_accounts: 0,
    active_accounts: 0,
    total_messages: 0,
    today_messages: 0,
    total_cost: 0,
    today_cost: 0,
  })
  const messageTrend = ref<{ date: string; count: number }[]>([])
  const costTrend = ref<{ date: string; cost: number }[]>([])
  const loading = ref(false)

  // Actions
  async function fetchStats() {
    loading.value = true
    try {
      const data = await dashboardApi.getStats()
      stats.value = data
    } catch (error) {
      console.error('获取统计数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchMessageTrend(days: number = 7) {
    try {
      const data = await dashboardApi.getMessageTrend(days)
      messageTrend.value = data
    } catch (error) {
      console.error('获取消息趋势失败:', error)
      messageTrend.value = []
    }
  }

  async function fetchCostTrend(days: number = 7) {
    try {
      const data = await dashboardApi.getCostTrend(days)
      costTrend.value = data
    } catch (error) {
      console.error('获取成本趋势失败:', error)
      costTrend.value = []
    }
  }

  return {
    stats,
    messageTrend,
    costTrend,
    loading,
    fetchStats,
    fetchMessageTrend,
    fetchCostTrend,
  }
})
