<template>
  <div class="dashboard">
    <!-- 统计卡片行 -->
    <div class="stats-row">
      <div
        v-for="(stat, idx) in stats"
        :key="stat.key"
        class="stat-card"
        :style="{ '--card-color': stat.color }"
      >
        <div class="stat-icon">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ stat.value }}</div>
        </div>
        <div class="stat-trend" :class="stat.trend >= 0 ? 'up' : 'down'">
          <el-icon><CaretTop v-if="stat.trend >= 0" /><CaretBottom v-else /></el-icon>
          {{ Math.abs(stat.trend) }}%
        </div>
      </div>
    </div>

    <!-- 主内容行 -->
    <div class="main-row">
      <!-- 左侧：灾害类型分布 + 各地市数量 -->
      <div class="left-col">
        <div class="card-panel chart-card">
          <div class="card-title">灾害类型分布</div>
          <v-chart class="chart" :option="pieOption" autoresize />
          <div class="chart-legend">
            <span
              v-for="item in typeDistribution"
              :key="item.name"
              class="legend-item"
            >
              <i class="dot" :style="{ background: item.color }"></i>
              {{ item.name }}
            </span>
          </div>
        </div>

        <div class="card-panel chart-card">
          <div class="card-title">各地市灾害数量</div>
          <v-chart class="chart bar-chart" :option="barOption" autoresize />
        </div>
      </div>

      <!-- 中间：地图 -->
      <div class="center-col">
        <div class="card-panel map-card">
          <div class="card-title">灾情态势地图</div>
          <div class="map-container">
            <DisasterMap :events="mapEvents" :focus-event="focusedEvent" />
          </div>
        </div>
      </div>

      <!-- 右侧：实时事件 + 趋势 -->
      <div class="right-col">
        <div class="card-panel event-card">
          <div class="card-title">
            实时事件流
            <el-tag size="small" type="success" effect="dark" round class="live-tag">
              <span class="pulse"></span>实时更新
            </el-tag>
            <el-button
              v-if="isResmanager && selectedEventIds.length > 0"
              type="primary"
              size="small"
              class="archive-btn"
              @click="handleArchive"
            >
              归档 ({{ selectedEventIds.length }})
            </el-button>
          </div>
          <div
            class="event-list"
            ref="eventListRef"
            @mouseenter="pauseAutoScroll"
            @mouseleave="resumeAutoScroll"
            @wheel="handleScrollInteraction"
          >            <div class="event-list-group">
              <div
                v-for="event in eventList"
                :key="event.id"
                class="event-item"
                :class="event.level"
                @click="focusEvent(event)"
              >
                <el-checkbox
                  v-if="isResmanager"
                  :model-value="selectedEventIds.includes(event.id)"
                  class="event-checkbox"
                  @click.stop
                  @update:model-value="checked => toggleEventSelection(event.id, checked)"
                />
                <div class="event-dot" :class="event.level"></div>
                <div class="event-body">
                  <div class="event-title">
                    <span class="event-type" :style="{ color: getDisasterColor(event.type) }">{{ event.type }}</span>
                    {{ event.title }}
                  </div>
                  <div class="event-meta">
                    <span><el-icon :size="12"><Location /></el-icon>{{ event.address }}</span>
                    <span class="event-time">{{ event.time }}</span>
                  </div>
                </div>
                <el-tag :type="statusTagType(event.status)" size="small" effect="light">
                  {{ event.status }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <div class="card-panel chart-card">
          <div class="card-title">近 7 日灾害趋势</div>
          <v-chart class="chart line-chart" :option="lineOption" autoresize />
        </div>
      </div>
    </div>

    <!-- 气象信息（灾情态势大屏下方） -->
    <WeatherPanel />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent
} from 'echarts/components'
import {
  getDashboardStats, getDisasterTypeDistribution, getCityDisasterCount,
  getWeeklyTrend, getMapMarkers, createArchiveFile
} from '@/api'
import { getDisasterColor } from '@/utils/constants'
import {
  Warning, CaretTop, CaretBottom
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import WeatherPanel from './WeatherPanel.vue'
import DisasterMap from './DisasterMap.vue'

use([
  CanvasRenderer,
  PieChart, BarChart, LineChart,
  TitleComponent, TooltipComponent, LegendComponent, GridComponent
])

const stats = ref([])
const typeDistribution = ref([])
const cityCount = ref([])
const weeklyTrend = ref([])
const mapMarkers = ref([])
const eventList = ref([])
const eventListRef = ref(null)
const autoScrollPaused = ref(false)
let autoScrollTimer = null
let resumeTimer = null

const userStore = useUserStore()
const isResmanager = computed(() => userStore.userInfo?.role === 'resmanager')
const selectedEventIds = ref([])
const focusedEvent = ref(null)

const cnTypeToEn = {
  '地震': 'EARTHQUAKE',
  '山洪': 'FLASH_FLOOD',
  '洪涝': 'FLOOD',
  '崩塌': 'COLLAPSE',
  '泥石流': 'DEBRIS_FLOW',
  '滑坡': 'LANDSLIDE',
  '暴雨': 'RAINSTORM'
}
const cnLevelToRoman = {
  '极高': 'I',
  '高': 'I',
  '中': 'II',
  '低': 'III'
}

const mapEvents = computed(() => {
  return mapMarkers.value.map(m => ({
    id: m.id,
    title: m.name,
    type: cnTypeToEn[m.type] || 'EARTHQUAKE',
    level: cnLevelToRoman[m.level] || 'IV',
    location: m.location || m.address || '',
    description: '',
    geo: { lng: parseFloat(m.lng), lat: parseFloat(m.lat) }
  })).filter(e => !isNaN(e.geo.lng) && !isNaN(e.geo.lat))
})

function getRiskColor(level) {
  const colors = {
    '特别重大': '#f5222d',
    '高': '#fa8c16',
    '中': '#faad14',
    '低': '#52c41a'
  }
  return colors[level] || '#1890ff'
}

const pieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  series: [{
    type: 'pie',
    radius: ['45%', '75%'],
    center: ['50%', '50%'],
    avoidLabelOverlap: true,
    itemStyle: {
      borderRadius: 6,
      borderColor: '#fff',
      borderWidth: 2
    },
    label: { show: false },
    emphasis: {
      label: { show: true, fontSize: 14, fontWeight: 'bold' }
    },
    data: typeDistribution.value.map(item => ({
      value: item.value,
      name: item.name,
      itemStyle: { color: item.color }
    }))
  }]
}))

const barOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '3%', bottom: '3%', top: '5%', containLabel: true },
  xAxis: {
    type: 'category',
    data: cityCount.value.map(d => (d.city || d.name || '').slice(0, 3)),
    axisLabel: { rotate: 45, fontSize: 10, interval: 0 },
    axisTick: { show: false },
    axisLine: { lineStyle: { color: '#e5e7eb' } }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f0f0f0' } },
    axisLabel: { show: false }
  },
  series: [{
    type: 'bar',
    data: cityCount.value.map(d => d.count || d.value),
    barWidth: 12,
    itemStyle: {
      borderRadius: [4, 4, 0, 0],
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: '#40a9ff' },
        { offset: 1, color: '#91caff' }
      ])
    }
  }]
}))

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '10%', right: '8%', bottom: '12%', top: '10%' },
  xAxis: {
    type: 'category',
    data: weeklyTrend.value.map(d => d.date),
    axisLabel: { fontSize: 10 },
    axisLine: { lineStyle: { color: '#e5e7eb' } }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f0f0f0' } },
    axisLabel: { fontSize: 10 }
  },
  series: [{
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    data: weeklyTrend.value.map(d => d.count),
    lineStyle: { color: '#36cfc9', width: 2 },
    itemStyle: { color: '#36cfc9' },
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(54, 207, 201, 0.3)' },
        { offset: 1, color: 'rgba(54, 207, 201, 0.05)' }
      ])
    }
  }]
}))

function statusTagType(status) {
  const map = {
    '待审核': 'warning',
    'pending': 'warning',
    '处置中': 'danger',
    'active': 'danger',
    'processing': 'danger',
    '已完成': 'success',
    'completed': 'success',
    '已确认': 'info',
    'confirmed': 'info',
    '已审核': 'info',
    'approved': 'info'
  }
  return map[status] || 'info'
}

// 实时事件流状态统一显示"处置中"
function normalizeStatus(status) {
  return '处置中'
}

// 常见受灾点坐标兜底（后端 incidents 表缺少经纬度时使用）
const fallbackCoordMap = {
  '东川': { lat: 26.083, lng: 103.182 },
  '墨江': { lat: 23.427, lng: 101.700 },
  '昆明': { lat: 25.0389, lng: 102.7183 },
  '普洱': { lat: 22.8252, lng: 100.9665 }
}

function resolveCoords(item) {
  const lat = item.lat ?? item.latitude
  const lng = item.lng ?? item.longitude
  if (lat != null && lng != null) {
    return { lat, lng }
  }
  const addr = (item.locationName || item.location_name || item.address || item.title || '').toString()
  for (const key of Object.keys(fallbackCoordMap)) {
    if (addr.includes(key)) return fallbackCoordMap[key]
  }
  return { lat: null, lng: null }
}

function focusEvent(event) {
  if (!event || (!event.lat && !event.lng)) {
    ElMessage.warning('该事件没有坐标信息，无法在地图上定位')
    return
  }
  focusedEvent.value = {
    id: event.id,
    title: event.title,
    type: cnTypeToEn[event.type] || 'EARTHQUAKE',
    level: cnLevelToRoman[event.level] || 'IV',
    location: event.address,
    geo: { lng: parseFloat(event.lng), lat: parseFloat(event.lat) }
  }
}

function toggleEventSelection(id, checked) {
  if (checked) {
    if (!selectedEventIds.value.includes(id)) {
      selectedEventIds.value.push(id)
    }
  } else {
    selectedEventIds.value = selectedEventIds.value.filter(x => x !== id)
  }
}

async function handleArchive() {
  if (selectedEventIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定归档选中的 ${selectedEventIds.value.length} 条实时事件吗？`,
      '归档确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  const selectedEvents = eventList.value.filter(e => selectedEventIds.value.includes(e.id))
  const payload = {
    content: JSON.stringify({
      archivedAt: new Date().toISOString(),
      count: selectedEvents.length,
      events: selectedEvents
    })
  }

  try {
    const res = await createArchiveFile(payload)
    if (res.code === 200 || res.success) {
      ElMessage.success('归档成功')
      eventList.value = eventList.value.filter(e => !selectedEventIds.value.includes(e.id))
      selectedEventIds.value = []
    } else {
      ElMessage.error(res.message || '归档失败')
    }
  } catch (e) {
    ElMessage.error(e.message || '归档失败')
  }
}

async function loadData() {
  selectedEventIds.value = []
  const results = await Promise.allSettled([
    getDashboardStats(),
    getDisasterTypeDistribution(),
    getCityDisasterCount(),
    getWeeklyTrend(),
    getMapMarkers()
  ])

  const [sRes, tRes, cRes, wRes, mRes] = results.map(r =>
    r.status === 'fulfilled' ? r.value : { success: false }
  )

  if (sRes?.code === 200) {
    const s = sRes.data || {}
    stats.value = [
      { key: 'total', label: '灾害总数', value: s.totalDisasters || 0, icon: 'Warning', color: '#f5222d', trend: 12 },
      { key: 'progress', label: '处置中', value: s.inProgress || 0, icon: 'Loading', color: '#fa8c16', trend: 5 },
      { key: 'pending', label: '待审核', value: s.pending || 0, icon: 'Clock', color: '#faad14', trend: -8 },
      { key: 'affected', label: '受灾人口', value: (s.affectedPeople || 0).toLocaleString(), icon: 'User', color: '#1890ff', trend: 3 },
      { key: 'resources', label: '可用资源', value: s.availableResources || 0, icon: 'Goods', color: '#52c41a', trend: 10 },
      { key: 'teams', label: '救援队伍', value: s.rescueTeams || 0, icon: 'Suitcase', color: '#722ed1', trend: 2 }
    ]
    // 实时事件流：后端 getDashboardStats 已解析 realtimeEvents → activeIncidents
    const events = s.activeIncidents || []
    eventList.value = events.map((item, index) => {
      const coords = resolveCoords(item)
      const id = item.id ?? item.incidentId ?? item.eventId ?? `event-${index}`
      return {
        id,
        level: item.riskLevel || item.risk_level || item.level || '中',
        type: item.disasterType || item.disaster_type || item.type || '其他',
        title: item.title || '',
        address: item.locationName || item.location_name || item.address || '',
        time: item.occurredAt || item.occurred_at || item.createdAt || item.time || '',
        status: normalizeStatus(item.status),
        lat: coords.lat,
        lng: coords.lng
      }
    })
    selectedEventIds.value = []
  }
  if (tRes?.code === 200) typeDistribution.value = tRes.data || []
  if (cRes?.code === 200) cityCount.value = cRes.data || []
  if (wRes?.code === 200) weeklyTrend.value = wRes.data || []
  if (mRes?.code === 200) {
    mapMarkers.value = mRes.data
  }
}

function startAutoScroll() {
  if (autoScrollTimer) return
  autoScrollTimer = setInterval(() => {
    if (autoScrollPaused.value) return
    const el = eventListRef.value
    if (!el) return
    if (el.scrollHeight <= el.clientHeight + 1) return
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 1) {
      el.scrollTop = 0
    } else {
      el.scrollTop += 1
    }
  }, 50)
}

function stopAutoScroll() {
  if (autoScrollTimer) {
    clearInterval(autoScrollTimer)
    autoScrollTimer = null
  }
}

function pauseAutoScroll() {
  autoScrollPaused.value = true
  if (resumeTimer) {
    clearTimeout(resumeTimer)
    resumeTimer = null
  }
}

function resumeAutoScroll() {
  autoScrollPaused.value = false
}

function handleScrollInteraction() {
  pauseAutoScroll()
  if (resumeTimer) clearTimeout(resumeTimer)
  resumeTimer = setTimeout(() => {
    autoScrollPaused.value = false
  }, 2000)
}

onMounted(() => {
  loadData()
  startAutoScroll()
  setInterval(loadData, 60000)
})

onBeforeUnmount(() => {
  stopAutoScroll()
  if (resumeTimer) clearTimeout(resumeTimer)
})
</script>

<style scoped lang="scss">
.dashboard {
  padding: 16px;
  height: 100%;
  overflow: auto;
  box-sizing: border-box;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--card-color);
    border-radius: 4px 0 0 4px;
  }
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: var(--card-color);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0.9;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  font-family: 'DIN Alternate', sans-serif;
}

.stat-trend {
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px;
  border-radius: 4px;

  &.up {
    color: #f5222d;
    background: rgba(245, 34, 45, 0.08);
  }

  &.down {
    color: #52c41a;
    background: rgba(82, 196, 26, 0.08);
  }
}

.main-row {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 16px;
  height: calc(100% - 110px);
}

.left-col,
.right-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.center-col {
  min-height: 0;
}

.card-panel {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  padding: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #1f2937;
  display: flex;
  align-items: center;
  justify-content: space-between;

  &::before {
    content: '';
    display: inline-block;
    width: 3px;
    height: 15px;
    background: #e64545;
    border-radius: 2px;
    margin-right: 8px;
    vertical-align: middle;
  }
}

.chart-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart {
  flex: 1;
  min-height: 180px;
}

.bar-chart {
  min-height: 220px;
}

.line-chart {
  min-height: 180px;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f3f4f6;
}

.legend-item {
  font-size: 11px;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 4px;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }
}

.map-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.map-container {
  flex: 1;
  min-height: 300px;
  border-radius: 6px;
  overflow: hidden;
  background: #f8fafc;
  position: relative;
}

.event-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.live-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;

  .pulse {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #52c41a;
    animation: blink 1.5s infinite;
  }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.event-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}

.event-list-group {
  display: contents;
}

.event-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px;
  border-radius: 6px;
  background: #f9fafb;
  transition: background 0.2s;
  cursor: pointer;

  &:hover {
    background: #eef2ff;
  }
}

.event-checkbox {
  margin-top: 2px;
  flex-shrink: 0;

  :deep(.el-checkbox__label) {
    display: none;
  }
}

.archive-btn {
  margin-left: auto;
}

.event-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;

  &.极高, &.高 { background: #f5222d; }
  &.中 { background: #faad14; }
  &.低 { background: #52c41a; }
}

.event-body {
  flex: 1;
  min-width: 0;
}

.event-title {
  font-size: 13px;
  color: #1f2937;
  margin-bottom: 4px;
  line-height: 1.4;
  font-weight: 500;
  word-break: break-all;
}

.event-type {
  font-weight: 600;
  margin-right: 4px;
}

.event-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  font-size: 11px;
  color: #9ca3af;
  gap: 2px;

  span {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

@media (max-width: 1400px) {
  .stats-row {
    grid-template-columns: repeat(3, 1fr);
  }

  .main-row {
    grid-template-columns: 1fr 1fr;
    height: auto;
  }

  .center-col {
    grid-column: 1 / -1;
    order: -1;

    .map-container {
      height: 400px;
    }
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 12px;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .stat-card {
    padding: 12px;

    .stat-value {
      font-size: 18px;
    }
  }

  .main-row {
    grid-template-columns: 1fr;
  }

  .map-container {
    min-height: 250px;
  }
}
</style>
