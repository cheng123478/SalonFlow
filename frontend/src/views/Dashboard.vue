<template>
  <div class="dashboard" v-loading="loading">
    <!-- 页头 -->
    <div class="page-head">
      <div>
        <div class="page-title">经营数据总览</div>
        <div class="page-sub">数据截至 {{ today }}</div>
      </div>
      <div class="head-actions">
        <el-button :icon="Refresh" circle @click="load" />
        <el-dropdown trigger="click" @command="onExport">
          <el-button type="primary" :icon="Download">
            导出报表
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="orders">订单 Excel</el-dropdown-item>
              <el-dropdown-item command="members">会员 Excel</el-dropdown-item>
              <el-dropdown-item command="reserves">预约 Excel</el-dropdown-item>
              <el-dropdown-item command="inventory">库存 Excel</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 营收核心指标 -->
    <div class="kpi-grid">
      <div v-for="k in kpis" :key="k.label" class="kpi-card">
        <div class="kpi-icon" :style="{ background: k.color + '1a', color: k.color }">
          <el-icon :size="22"><component :is="k.icon" /></el-icon>
        </div>
        <div class="kpi-info">
          <div class="kpi-value">
            {{ k.value }}<span v-if="k.unit" class="kpi-unit">{{ k.unit }}</span>
          </div>
          <div class="kpi-label">{{ k.label }}</div>
        </div>
      </div>
    </div>

    <!-- 图表区 -->
    <div class="chart-grid">
      <div class="col-8">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">营收趋势</span>
              <span class="panel-tag">近 30 天 · 已支付</span>
            </div>
          </template>
          <VChart v-if="hasDaily" :option="trendOption" height="300px" />
          <el-empty v-else description="暂无营收数据" :image-size="80" />
        </el-card>
      </div>

      <div class="col-4">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">预约状态分布</span>
            </div>
          </template>
          <VChart v-if="hasStatus" :option="statusOption" height="300px" />
          <el-empty v-else description="暂无预约数据" :image-size="80" />
        </el-card>
      </div>

      <div class="col-6">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">按技师营收</span>
              <span class="panel-tag">已支付</span>
            </div>
          </template>
          <VChart v-if="hasTechRevenue" :option="techRevenueOption" height="280px" />
          <el-empty v-else description="暂无营收数据" :image-size="80" />
        </el-card>
      </div>

      <div class="col-6">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">技师预约量</span>
            </div>
          </template>
          <VChart v-if="hasTechReserve" :option="techReserveOption" height="280px" />
          <el-empty v-else description="暂无预约数据" :image-size="80" />
        </el-card>
      </div>

      <div class="col-12">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">近 6 月新增会员</span>
            </div>
          </template>
          <VChart v-if="hasMonthly" :option="monthlyOption" height="260px" />
          <el-empty v-else description="暂无会员数据" :image-size="80" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowDown,
  Download,
  Money,
  Refresh,
  Tickets,
  TrendCharts,
  Wallet
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import VChart from '../components/VChart.vue'
import { getReserveStats, getRevenue, exportExcel } from '../api/report'

const loading = ref(false)
const revenue = ref({ summary: {}, daily: [], technician: [] })
const statusStats = ref([])
const technicianStats = ref([])
const monthlyStats = ref([])

const today = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
})

const STATUS_COLOR = {
  pending: '#F59E0B',
  confirmed: '#3B82F6',
  completed: '#10B981',
  cancelled: '#CBD5E1'
}
const STATUS_LABEL = {
  pending: '待确认',
  confirmed: '已确认',
  completed: '已完成',
  cancelled: '已取消'
}

const kpis = computed(() => [
  { icon: Money, label: '总营收（已支付）', value: fmtMoney(revenue.value.summary.total_paid), color: '#7C5CE7' },
  { icon: TrendCharts, label: '本月营收', value: fmtMoney(revenue.value.summary.month_paid), color: '#10B981' },
  { icon: Tickets, label: '订单总数', value: revenue.value.summary.order_count ?? '-', unit: '单', color: '#3B82F6' },
  { icon: Wallet, label: '待支付应收', value: fmtMoney(revenue.value.summary.total_unpaid), color: '#F59E0B' }
])

const hasDaily = computed(() => revenue.value.daily?.length > 0)
const hasStatus = computed(() => statusStats.value.length > 0)
const hasTechRevenue = computed(() => revenue.value.technician?.length > 0)
const hasTechReserve = computed(() => technicianStats.value.length > 0)
const hasMonthly = computed(() => monthlyStats.value.length > 0)

// 通用轴样式
const AXIS_LABEL = { color: '#94a3b8', fontSize: 11 }
const SPLIT_LINE = { lineStyle: { color: '#f1f5f9' } }

function fmtMoney(val) {
  if (val === null || val === undefined) return '-'
  return '¥' + Number(val).toFixed(2)
}

function axisMoney(v) {
  if (v >= 10000) return (v / 10000).toFixed(1) + '万'
  return String(v)
}

const moneyTooltip = { valueFormatter: (v) => '¥' + Number(v).toFixed(2) }

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis', ...moneyTooltip },
  grid: { left: 8, right: 16, top: 20, bottom: 4, containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: revenue.value.daily.map((d) => d.date),
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisTick: { show: false },
    axisLabel: { ...AXIS_LABEL, hideOverlap: true }
  },
  yAxis: {
    type: 'value',
    splitLine: SPLIT_LINE,
    axisLabel: { ...AXIS_LABEL, formatter: axisMoney }
  },
  series: [
    {
      name: '营收',
      type: 'line',
      smooth: true,
      showSymbol: false,
      symbol: 'circle',
      symbolSize: 6,
      data: revenue.value.daily.map((d) => Number(d.amount)),
      lineStyle: { width: 3, color: '#7C5CE7' },
      itemStyle: { color: '#7C5CE7', borderColor: '#fff', borderWidth: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(124, 92, 231, 0.26)' },
          { offset: 1, color: 'rgba(124, 92, 231, 0)' }
        ])
      }
    }
  ]
}))

const statusOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}：{c} 单（{d}%）' },
  legend: {
    bottom: 0,
    left: 'center',
    icon: 'circle',
    itemWidth: 8,
    itemHeight: 8,
    textStyle: { color: '#64748b', fontSize: 12 }
  },
  series: [
    {
      name: '预约状态',
      type: 'pie',
      radius: ['52%', '72%'],
      center: ['50%', '42%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        scaleSize: 6,
        label: { show: true, fontSize: 16, fontWeight: 600, color: '#1e293b' }
      },
      data: statusStats.value.map((s) => ({
        name: STATUS_LABEL[s.status] || s.status,
        value: s.count,
        itemStyle: { color: STATUS_COLOR[s.status] || '#CBD5E1' }
      }))
    }
  ]
}))

const techRevenueOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...moneyTooltip },
  grid: { left: 8, right: 24, top: 8, bottom: 4, containLabel: true },
  xAxis: {
    type: 'value',
    splitLine: SPLIT_LINE,
    axisLabel: { ...AXIS_LABEL, formatter: axisMoney }
  },
  yAxis: {
    type: 'category',
    data: [...revenue.value.technician].reverse().map((t) => t.technician),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#475569', fontSize: 12 }
  },
  series: [
    {
      name: '营收',
      type: 'bar',
      barWidth: 12,
      data: [...revenue.value.technician].reverse().map((t) => Number(t.amount)),
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#8B5CF6' },
          { offset: 1, color: '#6366F1' }
        ])
      }
    }
  ]
}))

const techReserveOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 8, right: 16, top: 20, bottom: 4, containLabel: true },
  xAxis: {
    type: 'category',
    data: technicianStats.value.map((t) => t.technician),
    axisTick: { show: false },
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: {
      ...AXIS_LABEL,
      interval: 0,
      rotate: technicianStats.value.length > 6 ? 20 : 0
    }
  },
  yAxis: {
    type: 'value',
    splitLine: SPLIT_LINE,
    minInterval: 1,
    axisLabel: AXIS_LABEL
  },
  series: [
    {
      name: '预约量',
      type: 'bar',
      barWidth: 16,
      data: technicianStats.value.map((t) => t.count),
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#38BDF8' },
          { offset: 1, color: '#3B82F6' }
        ])
      }
    }
  ]
}))

const monthlyOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 8, right: 16, top: 20, bottom: 4, containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: monthlyStats.value.map((m) => m.month),
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisTick: { show: false },
    axisLabel: AXIS_LABEL
  },
  yAxis: {
    type: 'value',
    splitLine: SPLIT_LINE,
    minInterval: 1,
    axisLabel: AXIS_LABEL
  },
  series: [
    {
      name: '新增会员',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      data: monthlyStats.value.map((m) => m.count),
      lineStyle: { width: 3, color: '#14B8A6' },
      itemStyle: { color: '#14B8A6', borderColor: '#fff', borderWidth: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(20, 184, 166, 0.22)' },
          { offset: 1, color: 'rgba(20, 184, 166, 0)' }
        ])
      }
    }
  ]
}))

async function load() {
  loading.value = true
  try {
    const [stats, rev] = await Promise.all([getReserveStats(), getRevenue()])
    statusStats.value = stats.data?.status || []
    technicianStats.value = stats.data?.technician || []
    monthlyStats.value = stats.data?.member_monthly || []
    revenue.value = rev.data || { summary: {}, daily: [], technician: [] }
  } catch (e) {
    // 拦截器已提示错误
  } finally {
    loading.value = false
  }
}

async function onExport(type) {
  try {
    await exportExcel(type)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error(e.message || '导出失败')
  }
}

onMounted(load)
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 页头 */
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}
.page-sub {
  margin-top: 4px;
  font-size: 13px;
  color: #94a3b8;
}
.head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* KPI 卡片 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.kpi-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  background: #fff;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.kpi-card:hover {
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  transform: translateY(-2px);
}
.kpi-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  flex-shrink: 0;
}
.kpi-info {
  min-width: 0;
}
.kpi-value {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
}
.kpi-unit {
  margin-left: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
}
.kpi-label {
  margin-top: 3px;
  font-size: 13px;
  color: #64748b;
}

/* 图表区 */
.chart-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}
.col-8 { grid-column: span 8; }
.col-6 { grid-column: span 6; }
.col-4 { grid-column: span 4; }
.col-12 { grid-column: span 12; }

.panel {
  border: 1px solid #f1f5f9;
  border-radius: 12px;
}
.panel :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f8fafc;
}
.panel :deep(.el-card__body) {
  padding: 12px 16px 16px;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}
.panel-tag {
  font-size: 12px;
  color: #94a3b8;
}

@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .col-8,
  .col-4,
  .col-6 {
    grid-column: span 12;
  }
}
</style>
