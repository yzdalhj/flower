<template>
  <div class="llm-usage-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-title">
        <span class="icon">🤖</span>
        <div>
          <h1>LLM 使用统计</h1>
          <p class="subtitle">监控和分析大模型 API 的使用情况与成本</p>
        </div>
      </div>
      <div class="header-actions">
        <t-radio-group v-model="timeRange" size="medium" variant="default-filled">
          <t-radio-button value="7">近7天</t-radio-button>
          <t-radio-button value="30">近30天</t-radio-button>
          <t-radio-button value="90">近90天</t-radio-button>
        </t-radio-group>
        <t-button theme="primary" @click="refreshData">
          <t-icon name="refresh" /> 刷新
        </t-button>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="metrics-section">
      <div class="metric-card" v-motion-slide-bottom :delay="100">
        <div class="metric-icon" style="background: linear-gradient(135deg, #667eea, #764ba2);">
          <t-icon name="chat" />
        </div>
        <div class="metric-content">
          <div class="metric-label">总请求数</div>
          <div class="metric-value">{{ formatNumber(dashboardData?.user_summary?.total_requests || 0) }}</div>
          <div class="metric-sub">{{ timeRange }}天内</div>
        </div>
      </div>

      <div class="metric-card" v-motion-slide-bottom :delay="200">
        <div class="metric-icon" style="background: linear-gradient(135deg, #4ecdc4, #44a08d);">
          <t-icon name="chart-bubble" />
        </div>
        <div class="metric-content">
          <div class="metric-label">Token 消耗</div>
          <div class="metric-value">{{ formatNumber(dashboardData?.user_summary?.total_tokens || 0) }}</div>
          <div class="metric-sub">
            输入: {{ formatNumber(dashboardData?.user_summary?.total_prompt_tokens || 0) }} |
            输出: {{ formatNumber(dashboardData?.user_summary?.total_completion_tokens || 0) }}
          </div>
        </div>
      </div>

      <div class="metric-card" v-motion-slide-bottom :delay="300">
        <div class="metric-icon" style="background: linear-gradient(135deg, #f093fb, #f5576c);">
          <t-icon name="money-circle" />
        </div>
        <div class="metric-content">
          <div class="metric-label">预估成本</div>
          <div class="metric-value">${{ (dashboardData?.user_summary?.total_cost || 0).toFixed(4) }}</div>
          <div class="metric-sub">USD</div>
        </div>
      </div>

      <div class="metric-card" v-motion-slide-bottom :delay="400">
        <div class="metric-icon" style="background: linear-gradient(135deg, #fdcb6e, #f39c12);">
          <t-icon name="clock" />
        </div>
        <div class="metric-content">
          <div class="metric-label">平均延迟</div>
          <div class="metric-value">{{ avgLatency }}ms</div>
          <div class="metric-sub">每次请求</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- Token 使用趋势 -->
      <div class="chart-card" v-motion-slide-bottom :delay="500">
        <div class="chart-header">
          <div class="chart-title">
            <span class="icon">📈</span>
            <span>Token 使用趋势</span>
          </div>
          <t-radio-group v-model="chartType" size="small" variant="default-filled">
            <t-radio-button value="tokens">Token</t-radio-button>
            <t-radio-button value="cost">成本</t-radio-button>
          </t-radio-group>
        </div>
        <div ref="trendChartRef" class="chart-body"></div>
      </div>

      <!-- 厂商分布 -->
      <div class="chart-card" v-motion-slide-bottom :delay="600">
        <div class="chart-header">
          <div class="chart-title">
            <span class="icon">🥧</span>
            <span>厂商使用分布</span>
          </div>
        </div>
        <div ref="providerChartRef" class="chart-body"></div>
      </div>
    </div>

    <!-- 操作类型统计 -->
    <div class="chart-card full-width" v-motion-slide-bottom :delay="700">
      <div class="chart-header">
        <div class="chart-title">
          <span class="icon">📊</span>
          <span>操作类型分布</span>
        </div>
      </div>
      <div ref="operationChartRef" class="chart-body" style="height: 300px;"></div>
    </div>

    <!-- 最近使用记录 -->
    <div class="records-section" v-motion-slide-bottom :delay="800">
      <div class="section-header">
        <div class="section-title">
          <span class="icon">📋</span>
          <span>最近使用记录</span>
        </div>
        <t-button theme="default" variant="text" size="small" @click="loadMoreRecords">
          查看更多
        </t-button>
      </div>
      <t-table
        :data="recentRecords"
        :columns="recordColumns"
        :loading="loading"
        stripe
        hover
        size="medium"
      >
        <template #provider="{ row }">
          <t-tag :theme="getProviderTheme(row.provider)" variant="light" size="small">
            {{ row.provider }}
          </t-tag>
        </template>
        <template #model="{ row }">
          <span class="model-text">{{ row.model }}</span>
        </template>
        <template #tokens="{ row }">
          <div class="tokens-cell">
            <span class="total">{{ row.total_tokens }}</span>
            <span class="detail">{{ row.prompt_tokens }} / {{ row.completion_tokens }}</span>
          </div>
        </template>
        <template #cost="{ row }">
          <span class="cost-text">${{ row.estimated_cost?.toFixed(6) }}</span>
        </template>
        <template #status="{ row }">
          <t-tag :theme="row.status === 'success' ? 'success' : 'danger'" variant="light" size="small">
            {{ row.status === 'success' ? '成功' : '失败' }}
          </t-tag>
        </template>
        <template #latency="{ row }">
          <span :class="['latency-text', getLatencyClass(row.latency_ms)]">
            {{ row.latency_ms }}ms
          </span>
        </template>
        <template #created_at="{ row }">
          <span class="time-text">{{ formatTime(row.created_at) }}</span>
        </template>
      </t-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { Chart } from '@antv/g2'
import { llmUsageApi, type DashboardData, type LLMUsageRecord } from '@/api/llmUsage'

const timeRange = ref('7')
const chartType = ref('tokens')
const loading = ref(false)
const dashboardData = ref<DashboardData | null>(null)
const recentRecords = ref<LLMUsageRecord[]>([])
const dailyStatistics = ref<any[]>([])

const trendChartRef = ref<HTMLElement>()
const providerChartRef = ref<HTMLElement>()
const operationChartRef = ref<HTMLElement>()

let trendChart: Chart | null = null
let providerChart: Chart | null = null
let operationChart: Chart | null = null

// 平均延迟
const avgLatency = computed(() => {
  if (!dashboardData.value?.operation_breakdown?.length) return 0
  const total = dashboardData.value.operation_breakdown.reduce((sum, op) => sum + (op.avg_latency_ms || 0), 0)
  return Math.round(total / dashboardData.value.operation_breakdown.length)
})

// 表格列定义
const recordColumns = [
  { colKey: 'provider', title: '厂商', width: 100 },
  { colKey: 'model', title: '模型', width: 150 },
  { colKey: 'operation', title: '操作', width: 150 },
  { colKey: 'tokens', title: 'Token (总/入/出)', width: 150 },
  { colKey: 'cost', title: '成本', width: 100 },
  { colKey: 'status', title: '状态', width: 80 },
  { colKey: 'latency', title: '延迟', width: 100 },
  { colKey: 'created_at', title: '时间', width: 180 },
]

// 获取厂商主题色
const getProviderTheme = (provider: string) => {
  const themes: Record<string, string> = {
    openai: 'primary',
    deepseek: 'success',
    kimi: 'warning',
    glm: 'danger',
  }
  return themes[provider.toLowerCase()] || 'default'
}

// 获取延迟样式
const getLatencyClass = (latency?: number) => {
  if (!latency) return ''
  if (latency < 1000) return 'fast'
  if (latency < 3000) return 'normal'
  return 'slow'
}

// 格式化数字
const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

// 格式化时间
const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const days = parseInt(timeRange.value)
    const [dashboard, records, dailyStats] = await Promise.all([
      llmUsageApi.getDashboard(days),
      llmUsageApi.getRecords(20),
      llmUsageApi.getDailyStatistics(days),
    ])
    dashboardData.value = dashboard
    recentRecords.value = records
    dailyStatistics.value = dailyStats
    updateCharts()
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  loadData()
}

// 加载更多记录
const loadMoreRecords = () => {
  // TODO: 实现分页加载
}

// 初始化趋势图表
const initTrendChart = () => {
  if (!trendChartRef.value) return
  trendChart = new Chart({
    container: trendChartRef.value,
    autoFit: true,
  })
}

// 初始化厂商分布图表
const initProviderChart = () => {
  if (!providerChartRef.value) return
  providerChart = new Chart({
    container: providerChartRef.value,
    autoFit: true,
  })
}

// 初始化操作类型图表
const initOperationChart = () => {
  if (!operationChartRef.value) return
  operationChart = new Chart({
    container: operationChartRef.value,
    autoFit: true,
  })
}

// 更新图表
const updateCharts = () => {
  updateTrendChart()
  updateProviderChart()
  updateOperationChart()
}

// 更新趋势图表
const updateTrendChart = () => {
  if (!trendChart || !dailyStatistics.value.length) return

  const data = dailyStatistics.value.map(d => ({
    date: d.stat_date.slice(5),
    tokens: d.total_tokens,
    cost: d.total_cost,
    input: d.total_prompt_tokens,
    output: d.total_completion_tokens,
  }))

  const isToken = chartType.value === 'tokens'

  trendChart.options({
    type: 'area',
    data,
    encode: { x: 'date', y: isToken ? 'tokens' : 'cost' },
    style: {
      fill: isToken
        ? 'linear-gradient(180deg, rgba(102, 126, 234, 0.3) 0%, rgba(102, 126, 234, 0.05) 100%)'
        : 'linear-gradient(180deg, rgba(240, 147, 251, 0.3) 0%, rgba(240, 147, 251, 0.05) 100%)',
      stroke: isToken ? '#667eea' : '#f093fb',
      lineWidth: 3,
    },
    axis: {
      x: { grid: false, labelFill: '#999' },
      y: { gridStroke: '#f0f0f0', labelFill: '#999' },
    },
    tooltip: {
      items: [
        { field: isToken ? 'tokens' : 'cost', name: isToken ? 'Token数' : '成本(USD)' },
        { field: 'input', name: '输入Token' },
        { field: 'output', name: '输出Token' },
      ],
    },
  })

  trendChart.render()
}

// 更新厂商分布图表
const updateProviderChart = () => {
  if (!providerChart || !dashboardData.value?.provider_breakdown?.length) return

  const data = dashboardData.value.provider_breakdown.map(p => ({
    provider: p.provider,
    tokens: p.total_tokens,
  }))

  providerChart.options({
    type: 'interval',
    data,
    coordinate: { type: 'theta', outerRadius: 0.8 },
    encode: { y: 'tokens', color: 'provider' },
    style: { radius: 8 },
    legend: { color: { position: 'right' } },
    tooltip: {
      items: [
        { field: 'tokens', name: 'Token数' },
        { field: 'provider', name: '厂商' },
      ],
    },
  })

  providerChart.render()
}

// 更新操作类型图表
const updateOperationChart = () => {
  if (!operationChart || !dashboardData.value?.operation_breakdown?.length) return

  const data = dashboardData.value.operation_breakdown.map(o => ({
    operation: o.operation,
    tokens: o.total_tokens,
    requests: o.total_requests,
  }))

  operationChart.options({
    type: 'interval',
    data,
    encode: { x: 'operation', y: 'tokens', color: 'operation' },
    style: { radius: [4, 4, 0, 0] },
    axis: {
      x: { labelFill: '#999', labelTransform: 'rotate(30)' },
      y: { gridStroke: '#f0f0f0', labelFill: '#999' },
    },
    tooltip: {
      items: [
        { field: 'tokens', name: 'Token数' },
        { field: 'requests', name: '请求数' },
      ],
    },
  })

  operationChart.render()
}

// 监听数据变化
watch(() => timeRange.value, loadData)
watch(() => chartType.value, updateTrendChart)

onMounted(() => {
  initTrendChart()
  initProviderChart()
  initOperationChart()
  loadData()

  window.addEventListener('resize', () => {
    trendChart?.forceFit()
    providerChart?.forceFit()
    operationChart?.forceFit()
  })
})
</script>

<style scoped>
.llm-usage-view {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100%;
  overflow-y: auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title .icon {
  font-size: 40px;
}

.header-title h1 {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  color: #333;
}

.subtitle {
  font-size: 14px;
  color: #999;
  margin: 4px 0 0 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 指标卡片 */
.metrics-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.metric-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  color: white;
  font-size: 28px;
}

.metric-content {
  flex: 1;
}

.metric-label {
  font-size: 14px;
  color: #999;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin-bottom: 4px;
}

.metric-sub {
  font-size: 12px;
  color: #999;
}

/* 图表区域 */
.charts-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.chart-card.full-width {
  grid-column: span 2;
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
  height: 300px;
}

/* 记录区域 */
.records-section {
  background: white;
  border-radius: 16px;
  padding: 20px;
  margin-top: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.section-title .icon {
  font-size: 20px;
}

/* 表格样式 */
.model-text {
  font-size: 12px;
  color: #666;
}

.tokens-cell {
  display: flex;
  flex-direction: column;
}

.tokens-cell .total {
  font-weight: 600;
  color: #333;
}

.tokens-cell .detail {
  font-size: 11px;
  color: #999;
}

.cost-text {
  font-family: 'SF Mono', monospace;
  color: #f5576c;
  font-weight: 500;
}

.latency-text {
  font-family: 'SF Mono', monospace;
}

.latency-text.fast {
  color: #00a870;
}

.latency-text.normal {
  color: #ff6b6d;
}

.latency-text.slow {
  color: #e34d59;
}

.time-text {
  font-size: 12px;
  color: #999;
}

@media (max-width: 1200px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
  .chart-card.full-width {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .header-actions {
    width: 100%;
  }
}
</style>
