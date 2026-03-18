<template>
  <div class="dashboard-view">
    <!-- 顶部欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1 class="welcome-title">👋 欢迎使用 AI小花</h1>
        <p class="welcome-subtitle">智能情感陪伴助手，让每一次对话都充满温度</p>
      </div>
      <div class="welcome-time">
        <div class="time-display">{{ currentTime }}</div>
        <div class="date-display">{{ currentDate }}</div>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="metrics-section">
      <div class="metric-card primary" v-motion-slide-bottom :delay="100">
        <div class="metric-bg-icon">💬</div>
        <div class="metric-content">
          <div class="metric-label">今日消息</div>
          <div class="metric-value">
            <span class="number">{{ formatNumber(dashboardStore.stats?.today_messages || 0) }}</span>
            <span class="trend" :class="messageTrend >= 0 ? 'up' : 'down'">
              <t-icon :name="messageTrend >= 0 ? 'arrow-up' : 'arrow-down'" />
              {{ Math.abs(messageTrend) }}%
            </span>
          </div>
          <div class="metric-footer">
            <t-progress :percentage="messageProgress" :color="'#667eea'" size="small" />
          </div>
        </div>
      </div>

      <div class="metric-card success" v-motion-slide-bottom :delay="200">
        <div class="metric-bg-icon">🌸</div>
        <div class="metric-content">
          <div class="metric-label">活跃账号</div>
          <div class="metric-value">
            <span class="number">{{ dashboardStore.stats?.active_accounts || 0 }}</span>
            <span class="unit">/{{ dashboardStore.stats?.total_accounts || 0 }}</span>
          </div>
          <div class="metric-footer">
            <div class="status-dots">
              <span
                v-for="i in dashboardStore.stats?.total_accounts || 0"
                :key="i"
                class="dot"
                :class="{ active: i <= (dashboardStore.stats?.active_accounts || 0) }"
              />
            </div>
          </div>
        </div>
      </div>

      <div class="metric-card warning" v-motion-slide-bottom :delay="300">
        <div class="metric-bg-icon">💰</div>
        <div class="metric-content">
          <div class="metric-label">今日成本</div>
          <div class="metric-value">
            <span class="currency">¥</span>
            <span class="number">{{ (dashboardStore.stats?.today_cost || 0).toFixed(2) }}</span>
          </div>
          <div class="metric-footer">
            <span class="budget-text">预算使用率 {{ costProgress }}%</span>
            <t-progress :percentage="costProgress" :color="costProgress > 80 ? '#e34d59' : '#ff6b6d'" size="small" />
          </div>
        </div>
      </div>

      <div class="metric-card info" v-motion-slide-bottom :delay="400">
        <div class="metric-bg-icon">📊</div>
        <div class="metric-content">
          <div class="metric-label">累计对话</div>
          <div class="metric-value">
            <span class="number">{{ formatNumber(dashboardStore.stats?.total_messages || 0) }}</span>
          </div>
          <div class="metric-footer">
            <span class="avg-text">平均 {{ avgMessagesPerDay }} 条/天</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-container message-chart" v-motion-slide-bottom :delay="500">
        <div class="chart-header">
          <div class="chart-title">
            <span class="icon">📈</span>
            <span>消息趋势</span>
          </div>
          <div class="chart-actions">
            <t-radio-group v-model="messagePeriod" size="small" variant="default-filled">
              <t-radio-button value="7">7天</t-radio-button>
              <t-radio-button value="30">30天</t-radio-button>
            </t-radio-group>
          </div>
        </div>
        <div ref="messageChartRef" class="chart-body"></div>
      </div>

      <div class="chart-container cost-chart" v-motion-slide-bottom :delay="600">
        <div class="chart-header">
          <div class="chart-title">
            <span class="icon">💵</span>
            <span>成本分析</span>
          </div>
          <div class="chart-actions">
            <t-radio-group v-model="costPeriod" size="small" variant="default-filled">
              <t-radio-button value="7">7天</t-radio-button>
              <t-radio-button value="30">30天</t-radio-button>
            </t-radio-group>
          </div>
        </div>
        <div ref="costChartRef" class="chart-body"></div>
      </div>
    </div>

    <!-- 底部区域 -->
    <div class="bottom-section">
      <!-- 活跃账号列表 -->
      <div class="panel accounts-panel" v-motion-slide-bottom :delay="700">
        <div class="panel-header">
          <div class="panel-title">
            <span class="icon">🚀</span>
            <span>活跃账号 TOP5</span>
          </div>
          <t-button theme="primary" variant="text" size="small" @click="goToAccounts">
            查看全部 <t-icon name="chevron-right" />
          </t-button>
        </div>
        <div class="panel-body">
          <div
            v-for="(account, index) in topAccounts"
            :key="account.id"
            class="account-item"
            :class="{ 'top-three': index < 3 }"
          >
            <div class="account-rank">{{ index + 1 }}</div>
            <div class="account-avatar">
              {{ account.platform === 'wechat' ? '💬' : '📱' }}
            </div>
            <div class="account-info">
              <div class="account-name">{{ account.name }}</div>
              <div class="account-platform">{{ account.platform }}</div>
            </div>
            <div class="account-stats">
              <div class="stat-item">
                <span class="stat-value">{{ account.today_message_count || 0 }}</span>
                <span class="stat-label">今日</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ formatNumber(account.total_message_count || 0) }}</span>
                <span class="stat-label">累计</span>
              </div>
            </div>
            <t-tag
              size="small"
              :theme="account.status === 'running' ? 'success' : 'default'"
              variant="light"
            >
              {{ account.status === 'running' ? '运行中' : '已停止' }}
            </t-tag>
          </div>
        </div>
      </div>

      <!-- 系统状态 -->
      <div class="panel status-panel" v-motion-slide-bottom :delay="800">
        <div class="panel-header">
          <div class="panel-title">
            <span class="icon">🔧</span>
            <span>系统状态</span>
          </div>
          <t-tag theme="success" variant="light" size="small">正常运行</t-tag>
        </div>
        <div class="panel-body">
          <div class="status-grid">
            <div class="status-card" v-for="status in systemStatus" :key="status.name">
              <div class="status-icon" :class="status.status">
                <t-icon :name="status.icon" />
              </div>
              <div class="status-info">
                <div class="status-name">{{ status.name }}</div>
                <div class="status-value" :class="status.status">{{ status.value }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷操作 -->
      <div class="panel quick-actions-panel" v-motion-slide-bottom :delay="900">
        <div class="panel-header">
          <div class="panel-title">
            <span class="icon">⚡</span>
            <span>快捷操作</span>
          </div>
        </div>
        <div class="panel-body">
          <div class="action-grid">
            <div class="action-item" @click="goTo('/admin/accounts')">
              <div class="action-icon" style="background: linear-gradient(135deg, #667eea, #764ba2);">
                <t-icon name="user" />
              </div>
              <span class="action-text">账号管理</span>
            </div>
            <div class="action-item" @click="goTo('/admin/conversations')">
              <div class="action-icon" style="background: linear-gradient(135deg, #4ecdc4, #44a08d);">
                <t-icon name="chat" />
              </div>
              <span class="action-text">对话记录</span>
            </div>
            <div class="action-item" @click="goTo('/admin/users')">
              <div class="action-icon" style="background: linear-gradient(135deg, #f093fb, #f5576c);">
                <t-icon name="user-group" />
              </div>
              <span class="action-text">用户管理</span>
            </div>
            <div class="action-item" @click="goTo('/admin/settings')">
              <div class="action-icon" style="background: linear-gradient(135deg, #fdcb6e, #f39c12);">
                <t-icon name="setting" />
              </div>
              <span class="action-text">系统设置</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore, useAccountStore } from '@/stores'
import { Chart } from '@antv/g2'
import type { Account } from '@/types'

const router = useRouter()
const dashboardStore = useDashboardStore()
const accountStore = useAccountStore()

const messageChartRef = ref<HTMLElement>()
const costChartRef = ref<HTMLElement>()
const messagePeriod = ref('7')
const costPeriod = ref('7')
const currentTime = ref('')
const currentDate = ref('')

let messageChart: Chart | null = null
let costChart: Chart | null = null

// 更新时间
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  currentDate.value = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
}

// 计算趋势
const messageTrend = computed(() => {
  const messages = dashboardStore.messageTrend
  if (messages.length < 2) return 0
  const today = messages[messages.length - 1]?.count || 0
  const yesterday = messages[messages.length - 2]?.count || 0
  if (yesterday === 0) return 0
  return Math.round(((today - yesterday) / yesterday) * 100)
})

// 消息进度（假设日目标1000条）
const messageProgress = computed(() => {
  const today = dashboardStore.stats?.today_messages || 0
  return Math.min(Math.round((today / 1000) * 100), 100)
})

// 成本进度（假设日预算50元）
const costProgress = computed(() => {
  const today = dashboardStore.stats?.today_cost || 0
  return Math.min(Math.round((today / 50) * 100), 100)
})

// 平均每日消息
const avgMessagesPerDay = computed(() => {
  const total = dashboardStore.stats?.total_messages || 0
  return Math.round(total / 30)
})

// TOP5 活跃账号
const topAccounts = computed(() => {
  return [...accountStore.accounts]
    .sort((a, b) => (b.today_message_count || 0) - (a.today_message_count || 0))
    .slice(0, 5)
})

// 系统状态
const systemStatus = ref([
  { name: 'API服务', icon: 'internet', status: 'success', value: '正常' },
  { name: '数据库', icon: 'server', status: 'success', value: '正常' },
  { name: 'Redis', icon: 'memory', status: 'success', value: '正常' },
  { name: '消息队列', icon: 'queue', status: 'success', value: '正常' },
])

// 初始化消息趋势图表
const initMessageChart = () => {
  if (!messageChartRef.value) return

  messageChart = new Chart({
    container: messageChartRef.value,
    autoFit: true,
  })

  updateMessageChart()
}

// 更新消息趋势图表
const updateMessageChart = () => {
  if (!messageChart) return

  const data = dashboardStore.messageTrend.map(d => ({
    date: d.date.slice(5),
    count: d.count,
  }))

  messageChart.options({
    type: 'area',
    data,
    encode: { x: 'date', y: 'count' },
    style: {
      fill: 'linear-gradient(180deg, rgba(102, 126, 234, 0.3) 0%, rgba(102, 126, 234, 0.05) 100%)',
      stroke: '#667eea',
      lineWidth: 3,
    },
    axis: {
      x: {
        grid: false,
        labelFill: '#999',
        lineStroke: '#e7e7e7',
      },
      y: {
        gridStroke: '#f0f0f0',
        labelFill: '#999',
      },
    },
    tooltip: {
      items: [
        { field: 'count', name: '消息数', valueFormatter: (v: number) => `${v}` },
      ],
    },
    interaction: { tooltip: true },
  })

  messageChart.render()
}

// 初始化成本图表
const initCostChart = () => {
  if (!costChartRef.value) return

  costChart = new Chart({
    container: costChartRef.value,
    autoFit: true,
  })

  updateCostChart()
}

// 更新成本图表
const updateCostChart = () => {
  if (!costChart) return

  const data = dashboardStore.costTrend.map(d => ({
    date: d.date.slice(5),
    cost: d.cost,
  }))

  costChart.options({
    type: 'interval',
    data,
    encode: { x: 'date', y: 'cost' },
    style: {
      fill: 'linear-gradient(180deg, #ff6b6d 0%, #ff8e8e 100%)',
      radius: [4, 4, 0, 0],
    },
    axis: {
      x: {
        grid: false,
        labelFill: '#999',
        lineStroke: '#e7e7e7',
      },
      y: {
        gridStroke: '#f0f0f0',
        labelFill: '#999',
        labelFormatter: (v: number) => `¥${v}`,
      },
    },
    tooltip: {
      items: [
        { field: 'cost', name: '成本', valueFormatter: (v: number) => `¥${v.toFixed(2)}` },
      ],
    },
    interaction: { tooltip: true },
  })

  costChart.render()
}

// 格式化数字
const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

// 导航
const goTo = (path: string) => router.push(path)
const goToAccounts = () => router.push('/admin/accounts')

// 监听数据变化
watch(() => dashboardStore.messageTrend, updateMessageChart, { deep: true })
watch(() => dashboardStore.costTrend, updateCostChart, { deep: true })

watch(messagePeriod, async (days) => {
  await dashboardStore.fetchMessageTrend(Number(days))
})

watch(costPeriod, async (days) => {
  await dashboardStore.fetchCostTrend(Number(days))
})

onMounted(async () => {
  updateTime()
  setInterval(updateTime, 60000)

  await dashboardStore.fetchStats()
  await dashboardStore.fetchMessageTrend(Number(messagePeriod.value))
  await dashboardStore.fetchCostTrend(Number(costPeriod.value))
  await accountStore.fetchAccounts()

  initMessageChart()
  initCostChart()

  window.addEventListener('resize', () => {
    messageChart?.forceFit()
    costChart?.forceFit()
  })
})
</script>

<style scoped>
.dashboard-view {
  padding: 24px;
  background: #f5f7fa;
  overflow-y: auto;
}

/* 欢迎区域 */
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.welcome-subtitle {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.welcome-time {
  text-align: right;
}

.time-display {
  font-size: 36px;
  font-weight: 700;
  font-family: 'SF Mono', monospace;
}

.date-display {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

/* 核心指标卡片 */
.metrics-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.metric-card {
  position: relative;
  padding: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
}

.metric-bg-icon {
  position: absolute;
  right: -20px;
  bottom: -20px;
  font-size: 120px;
  opacity: 0.05;
  pointer-events: none;
}

.metric-content {
  position: relative;
  z-index: 1;
}

.metric-label {
  font-size: 14px;
  color: #999;
  margin-bottom: 12px;
}

.metric-value {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}

.metric-value .number {
  font-size: 36px;
  font-weight: 700;
  color: #333;
}

.metric-value .unit {
  font-size: 18px;
  color: #999;
}

.metric-value .currency {
  font-size: 24px;
  font-weight: 600;
  color: #ff6b6d;
}

.metric-value .trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
}

.metric-value .trend.up {
  color: #00a870;
  background: rgba(0, 168, 112, 0.1);
}

.metric-value .trend.down {
  color: #e34d59;
  background: rgba(227, 77, 89, 0.1);
}

.metric-footer {
  margin-top: 8px;
}

.status-dots {
  display: flex;
  gap: 6px;
}

.status-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e7e7e7;
  transition: background 0.3s;
}

.status-dots .dot.active {
  background: #00a870;
}

.budget-text, .avg-text {
  font-size: 12px;
  color: #999;
  display: block;
  margin-bottom: 8px;
}

/* 图表区域 */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.chart-container {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.chart-title .icon {
  font-size: 20px;
}

.chart-body {
  height: 280px;
}

/* 底部区域 */
.bottom-section {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 20px;
}

@media (max-width: 1200px) {
  .bottom-section {
    grid-template-columns: 1fr 1fr;
  }
  .quick-actions-panel {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .bottom-section {
    grid-template-columns: 1fr;
  }
  .quick-actions-panel {
    grid-column: span 1;
  }
}

/* 面板通用样式 */
.panel {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.panel-title .icon {
  font-size: 20px;
}

.panel-body {
  padding: 16px 20px;
}

/* 账号列表 */
.account-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 8px;
  transition: background 0.3s;
}

.account-item:hover {
  background: #f8f9fa;
}

.account-item.top-three .account-rank {
  background: linear-gradient(135deg, #ffd700, #ffaa00);
  color: white;
}

.account-rank {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  color: #999;
}

.account-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 10px;
  font-size: 20px;
}

.account-info {
  flex: 1;
  min-width: 0;
}

.account-name {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.account-platform {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.account-stats {
  display: flex;
  gap: 16px;
  margin-right: 12px;
}

.stat-item {
  text-align: center;
}

.stat-item .stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #667eea;
}

.stat-item .stat-label {
  font-size: 11px;
  color: #999;
}

/* 系统状态 */
.status-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
}

.status-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 20px;
}

.status-icon.success {
  background: rgba(0, 168, 112, 0.1);
  color: #00a870;
}

.status-info {
  flex: 1;
}

.status-name {
  font-size: 13px;
  color: #999;
  margin-bottom: 4px;
}

.status-value {
  font-size: 15px;
  font-weight: 600;
}

.status-value.success {
  color: #00a870;
}

/* 快捷操作 */
.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-item:hover {
  background: white;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.action-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: white;
  font-size: 24px;
}

.action-text {
  font-size: 13px;
  font-weight: 500;
  color: #666;
}
</style>
