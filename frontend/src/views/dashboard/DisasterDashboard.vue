<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, onActivated, onDeactivated, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useDisasterStore } from '@/stores/disaster'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import DisasterMap from '@/components/DisasterMap.vue'
import StatCard from '@/components/StatCard.vue'
import EChart from '@/components/EChart.vue'
import EventTicker from '@/components/EventTicker.vue'
import { USE_MOCK } from '@/api/mock'
import { openWs } from '@/utils/websocket'
import { getToken } from '@/utils/auth'
import type { RealtimeEvent } from '@/types'

const disaster = useDisasterStore()
const auth = useAuthStore()
const notifications = useNotificationsStore()
const { list, stat, typeCount, cityCount, trend } = storeToRefs(disaster)

const realtime = ref<RealtimeEvent[]>([])
const connected = ref(false)
let ws: { close: () => void } | null = null
let timer: number | null = null
let rid = 1

const typeLabel: Record<string, string> = {
  EARTHQUAKE: '地震',
  FLOOD: '洪涝',
  LANDSLIDE: '滑坡',
  DEBRIS_FLOW: '泥石流',
  DROUGHT: '干旱',
  FOREST_FIRE: '森林火灾',
  HAIL: '冰雹',
  TYPHOON: '台风'
}
const statusLabel: Record<string, string> = {
  PENDING_VERIFY: '待核验',
  CONFIRMED: '已确认',
  IN_PROGRESS: '处置中',
  CLOSED: '已结束',
  REJECTED: '已驳回'
}

function pushRealtime(e: RealtimeEvent) {
  realtime.value.unshift(e)
  if (realtime.value.length > 50) realtime.value.pop()
}

// Mock 模式下模拟实时事件流
function startMockFeed() {
  connected.value = true
  const messages: { type: RealtimeEvent['type']; msg: (d: any) => string }[] = [
    { type: 'NEW', msg: (d) => `新增灾情上报：${d.title}` },
    { type: 'STATUS_CHANGE', msg: (d) => `${d.title} 状态变更为「${statusLabel[(d.status as string)]}」` },
    { type: 'DISPATCH', msg: (d) => `已向 ${d.city} 调度救援资源` },
    { type: 'PLAN', msg: (d) => `AI 已生成 ${d.title} 处置方案` }
  ]
  timer = window.setInterval(() => {
    if (!list.value.length) return
    const d = list.value[Math.floor(Math.random() * list.value.length)]
    const m = messages[Math.floor(Math.random() * messages.length)]
    const event = {
      id: rid++,
      eventId: d.id,
      eventCode: d.code,
      type: m.type,
      message: m.msg(d),
      status: d.status as any,
      createdAt: new Date().toISOString()
    }
    pushRealtime(event)
    // 关键事件联动消息盒子（避免刷屏：仅新增灾情 / 资源调度）
    if (m.type === 'NEW' || m.type === 'DISPATCH') {
      notifications.push({
        type: m.type === 'NEW' ? 'urgent' : 'success',
        title: m.type === 'NEW' ? `新灾情上报：${d.title}` : '救援资源已调度',
        body: m.msg(d),
        ts: Date.now(),
        from: m.type === 'NEW' ? '灾情监测' : '资源调度'
      })
    }
  }, 4500)
}

// 统一启动实时流（带重复启动保护）
function startFeed() {
  if (timer || ws) return
  if (USE_MOCK) startMockFeed()
  else startRealFeed()
}

// 停止实时流（离开页面 / 组件销毁时调用，避免后台持续推送造成卡顿与通知堆积）
function stopFeed() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  ws?.close()
  ws = null
  connected.value = false
}

function startRealFeed() {
  ws = openWs(
    import.meta.env.VITE_WS_BASE,
    {
      onOpen: () => (connected.value = true),
      onMessage: (data) => pushRealtime(data as RealtimeEvent),
      onError: () => (connected.value = false),
      onClose: () => (connected.value = false)
    },
    getToken()
  )
}

const palette = ['#e03e2f', '#f2994a', '#2f80ed', '#27ae60', '#8e44ad', '#16a085', '#e67e22', '#2980b9']

// 图表配置
const pieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0, type: 'scroll', icon: 'circle' },
  color: palette,
  series: [
    {
      type: 'pie',
      radius: ['42%', '70%'],
      center: ['50%', '44%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 6 },
      label: { show: false },
      data: typeCount.value.map((t) => ({ name: typeLabel[t.type] || t.type, value: t.count }))
    }
  ]
}))

const barOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 50, right: 16, top: 16, bottom: 56 },
  xAxis: {
    type: 'category',
    data: cityCount.value.map((c) => c.city),
    axisLabel: { interval: 0, rotate: 35, fontSize: 11, color: '#7a8794' },
    axisLine: { lineStyle: { color: '#e6eaf1' } }
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#7a8794' },
    splitLine: { lineStyle: { color: '#f0f2f6' } }
  },
  series: [
    {
      type: 'bar',
      data: cityCount.value.map((c) => c.count),
      barWidth: '46%',
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: '#f2994a' },
            { offset: 1, color: '#e03e2f' }
          ]
        }
      }
    }
  ]
}))

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 16, top: 16, bottom: 30 },
  xAxis: {
    type: 'category',
    data: trend.value.map((t) => t.date),
    axisLabel: { color: '#7a8794' },
    axisLine: { lineStyle: { color: '#e6eaf1' } }
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#7a8794' },
    splitLine: { lineStyle: { color: '#f0f2f6' } }
  },
  series: [
    {
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      data: trend.value.map((t) => t.count),
      lineStyle: { width: 3, color: '#2f80ed' },
      itemStyle: { color: '#2f80ed' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(47,128,237,.28)' },
            { offset: 1, color: 'rgba(47,128,237,0)' }
          ]
        }
      }
    }
  ]
}))

onMounted(async () => {
  await disaster.fetchStat()
  await disaster.fetchList({ pageSize: 100 })
})

// 进入页面（含 keep-alive 重新激活）时启动实时流
onActivated(() => {
  startFeed()
})

// 离开页面（含 keep-alive 缓存）时停止，避免后台定时器持续推送
onDeactivated(() => {
  stopFeed()
})

onBeforeUnmount(() => {
  stopFeed()
})
</script>

<template>
  <div class="dashboard">
    <!-- 指令条 -->
    <div class="cmdbar">
      <div class="cmd-title"><span class="bar"></span> 灾情态势总览</div>
      <div class="cmd-meta">
        <span class="dot" :class="{ on: connected }"></span>
        {{ connected ? '实时连接' : '模拟推送' }} · 数据更新于 {{ new Date().toLocaleTimeString() }}
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats">
      <StatCard title="灾情总数" :value="stat?.eventTotal ?? 0" icon="Warning" color="#e03e2f" />
      <StatCard title="处置中" :value="stat?.handlingCount ?? 0" icon="Loading" color="#f2994a" />
      <StatCard title="待核验" :value="stat?.pendingVerifyCount ?? 0" icon="Bell" color="#e6a23c" />
      <StatCard title="受影响人口" :value="(stat?.affectedPopulation ?? 0).toLocaleString()" icon="User" color="#2f80ed" />
      <StatCard title="可调资源" :value="stat?.resourceIdle ?? 0" icon="Box" color="#27ae60" />
      <StatCard title="伤亡(人)" :value="stat?.casualties ?? 0" icon="FirstAidKit" color="#8e44ad" />
    </div>

    <div class="grid">
      <!-- 地图 -->
      <div class="panel map-panel">
        <div class="panel-title">灾情态势地图</div>
        <div class="map-wrap">
          <DisasterMap :events="list" />
        </div>
      </div>

      <!-- 实时事件 -->
      <div class="panel">
        <div class="panel-title">实时事件流</div>
        <EventTicker :events="realtime" :connected="connected" />
      </div>
    </div>

    <div class="grid charts">
      <div class="panel">
        <div class="panel-title">灾害类型分布</div>
        <EChart :option="pieOption" height="260px" />
      </div>
      <div class="panel">
        <div class="panel-title">各地州灾情数量</div>
        <EChart :option="barOption" height="260px" />
      </div>
      <div class="panel">
        <div class="panel-title">近 7 日灾情趋势</div>
        <EChart :option="lineOption" height="260px" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.cmdbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: linear-gradient(90deg, #ffffff, #fbfcfd);
  border: 1px solid var(--ydr-border);
  border-radius: 12px;
  box-shadow: var(--ydr-shadow);
}
.cmd-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--ydr-ink);
}
.cmd-title .bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--ydr-primary);
}
.cmd-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--ydr-sub);
}
.cmd-meta .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #bdc3c7;
}
.cmd-meta .dot.on {
  background: #27ae60;
  box-shadow: 0 0 0 3px rgba(39, 174, 96, 0.25);
  animation: pulse 1.4s infinite;
}
@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(39, 174, 96, 0.5);
  }
  100% {
    box-shadow: 0 0 0 6px rgba(39, 174, 96, 0);
  }
}
.stats {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
}
.grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}
.grid.charts {
  grid-template-columns: repeat(3, 1fr);
}
.panel {
  background: #fff;
  border: 1px solid var(--ydr-border);
  border-radius: 12px;
  padding: 16px;
  box-shadow: var(--ydr-shadow);
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s ease;
}
.panel:hover {
  box-shadow: var(--ydr-shadow-lg);
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--ydr-ink);
}
.panel-title::before {
  content: '';
  width: 4px;
  height: 15px;
  border-radius: 2px;
  background: var(--ydr-primary);
}
.map-wrap {
  flex: 1;
  min-height: 440px;
}
@media (max-width: 1200px) {
  .stats {
    grid-template-columns: repeat(3, 1fr);
  }
  .grid,
  .grid.charts {
    grid-template-columns: 1fr;
  }
}

/* 指标卡错峰入场（指数减速，焦点集中于关键数据） */
.stats :deep(.stat-card) {
  animation: ydr-rise 0.55s var(--ease-out-expo) both;
}
.stats :deep(.stat-card):nth-child(1) {
  animation-delay: 0.05s;
}
.stats :deep(.stat-card):nth-child(2) {
  animation-delay: 0.1s;
}
.stats :deep(.stat-card):nth-child(3) {
  animation-delay: 0.15s;
}
.stats :deep(.stat-card):nth-child(4) {
  animation-delay: 0.2s;
}
.stats :deep(.stat-card):nth-child(5) {
  animation-delay: 0.25s;
}
.stats :deep(.stat-card):nth-child(6) {
  animation-delay: 0.3s;
}
.stats :deep(.stat-card):nth-child(7) {
  animation-delay: 0.35s;
}
</style>
