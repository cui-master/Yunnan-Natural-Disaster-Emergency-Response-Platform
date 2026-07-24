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
let clockTimer: number | null = null
const now = ref(new Date())

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

const palette = ['#36e0c8', '#ffb547', '#4aa8ff', '#5ee06b', '#b07cff', '#ff6b8a', '#ffd166', '#4cc9f0']

// 图表配置（光明大屏风格）
const TEXT = '#334155'
const SUB = '#64748b'
const AXIS = '#cbd5e1'
const SPLIT = '#e2e8f0'

const pieOption = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { color: TEXT },
  tooltip: { trigger: 'item', backgroundColor: 'rgba(255,255,255,0.96)', borderColor: '#e2e8f0', textStyle: { color: TEXT }, formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0, type: 'scroll', icon: 'circle', textStyle: { color: SUB } },
  color: palette,
  series: [
    {
      type: 'pie',
      radius: ['42%', '70%'],
      center: ['50%', '44%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 6 },
      label: { color: TEXT, fontSize: 11 },
      labelLine: { lineStyle: { color: SUB } },
      data: typeCount.value.map((t) => ({ name: typeLabel[t.type] || t.type, value: t.count }))
    }
  ]
}))

const barOption = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { color: TEXT },
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: 'rgba(255,255,255,0.96)', borderColor: '#e2e8f0', textStyle: { color: TEXT } },
  grid: { left: 46, right: 16, top: 16, bottom: 56 },
  xAxis: {
    type: 'category',
    data: cityCount.value.map((c) => c.city),
    axisLabel: { interval: 0, rotate: 35, fontSize: 11, color: SUB },
    axisLine: { lineStyle: { color: AXIS } },
    axisTick: { show: false }
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: SUB },
    splitLine: { lineStyle: { color: SPLIT } }
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
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#4cc9f0' },
            { offset: 1, color: '#2563eb' }
          ]
        }
      }
    }
  ]
}))

const lineOption = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { color: TEXT },
  tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.96)', borderColor: '#e2e8f0', textStyle: { color: TEXT } },
  grid: { left: 40, right: 16, top: 16, bottom: 30 },
  xAxis: {
    type: 'category',
    data: trend.value.map((t) => t.date),
    axisLabel: { color: SUB, fontSize: 11 },
    axisLine: { lineStyle: { color: AXIS } },
    axisTick: { show: false }
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: SUB },
    splitLine: { lineStyle: { color: SPLIT } }
  },
  series: [
    {
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      data: trend.value.map((t) => t.count),
      lineStyle: { width: 3, color: '#36e0c8' },
      itemStyle: { color: '#36e0c8' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(54,224,200,0.32)' },
            { offset: 1, color: 'rgba(54,224,200,0)' }
          ]
        }
      }
    }
  ]
}))

onMounted(async () => {
  await disaster.fetchStat()
  await disaster.fetchList({ pageSize: 100 })
  clockTimer = window.setInterval(() => (now.value = new Date()), 1000)
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
  if (clockTimer) clearInterval(clockTimer)
})

const dateText = computed(() => {
  const d = now.value
  const w = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} 星期${w}`
})
const timeText = computed(() => now.value.toLocaleTimeString('zh-CN', { hour12: false }))
</script>

<template>
  <div class="screen">
    <!-- 大屏标题栏 -->
    <header class="scr-header">
      <div class="scr-side scr-left">
        <span class="scr-date">{{ dateText }}</span>
      </div>
      <h1 class="scr-title">
        <span class="scr-title-main">云南自然灾害应急协同决策平台</span>
        <span class="scr-title-sub">灾情态势大屏 · COMMAND CENTER</span>
      </h1>
      <div class="scr-side scr-right">
        <span class="scr-clock">{{ timeText }}</span>
        <span class="scr-net" :class="{ on: connected }">
          <i class="scr-dot"></i>{{ connected ? '实时链路' : '模拟推送' }}
        </span>
      </div>
    </header>

    <!-- KPI 发光数字行 -->
    <section class="kpi-row">
      <StatCard title="灾情总数" :value="stat?.eventTotal ?? 0" icon="Warning" color="#ff6b6b" />
      <StatCard title="处置中" :value="stat?.handlingCount ?? 0" icon="Loading" color="#ffb547" />
      <StatCard title="待核验" :value="stat?.pendingVerifyCount ?? 0" icon="Bell" color="#ffd166" />
      <StatCard title="受影响人口" :value="(stat?.affectedPopulation ?? 0).toLocaleString()" icon="User" color="#4cc9f0" />
      <StatCard title="可调资源" :value="stat?.resourceIdle ?? 0" icon="Box" color="#5ee06b" />
      <StatCard title="伤亡(人)" :value="stat?.casualties ?? 0" icon="FirstAidKit" color="#b07cff" />
    </section>

    <!-- 主体三栏 -->
    <section class="scr-body">
      <!-- 左栏：图表 -->
      <div class="col">
        <div class="panel">
          <div class="panel-title">灾害类型分布</div>
          <div class="chart-box"><EChart :option="pieOption" height="100%" /></div>
        </div>
        <div class="panel">
          <div class="panel-title">各地州灾情数量</div>
          <div class="chart-box"><EChart :option="barOption" height="100%" /></div>
        </div>
      </div>

      <!-- 中栏：地图 -->
      <div class="col col-map">
        <div class="panel panel-map">
          <div class="panel-title">灾情态势地图</div>
          <div class="map-wrap">
            <DisasterMap :events="list" />
          </div>
          <div class="map-foot">
            <span>实时监测 · 云南省</span>
            <span>事件 {{ stat?.eventTotal ?? 0 }} · 处置中 {{ stat?.handlingCount ?? 0 }}</span>
          </div>
        </div>
      </div>

      <!-- 右栏：实时事件 + 趋势 -->
      <div class="col">
        <div class="panel panel-ticker">
          <div class="panel-title">实时事件流</div>
          <EventTicker :events="realtime" :connected="connected" />
        </div>
        <div class="panel">
          <div class="panel-title">近 7 日灾情趋势</div>
          <div class="chart-box"><EChart :option="lineOption" height="100%" /></div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.screen {
  /* 满血铺满内容区（相对 .main 绝对定位，无视 padding，形成全屏大屏） */
  position: absolute;
  inset: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  padding: 14px 18px 16px;
  gap: 12px;
  overflow: hidden;
  color: #334155;
  background: #f1f5f9;
}

/* ===== 标题栏 ===== */
.scr-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 58px;
  flex-shrink: 0;
}
.scr-title {
  text-align: center;
  line-height: 1.1;
}
.scr-title-main {
  display: block;
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 3px;
  color: #0f172a;
}
.scr-title-sub {
  display: block;
  font-size: 11px;
  letter-spacing: 4px;
  color: #64748b;
  margin-top: 2px;
}
.scr-side {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 280px;
}
.scr-right { justify-content: flex-end; }
.scr-date { font-size: 14px; color: #475569; letter-spacing: 1px; }
.scr-clock {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: #0ea5e9;
  letter-spacing: 1px;
  font-variant-numeric: tabular-nums;
}
.scr-net {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  color: #d97706;
  background: #fffbeb;
  border: 1px solid #fcd34d;
}
.scr-net.on { color: #16a34a; background: #f0fdf4; border-color: #86efac; }
.scr-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }

/* ===== KPI 行 ===== */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  flex-shrink: 0;
}

/* ===== 主体三栏 ===== */
.scr-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1.55fr 1fr;
  gap: 12px;
}
.col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}
.col-map { min-height: 0; }

/* ===== 面板（白底卡片） ===== */
.panel {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 12px 14px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 10px;
  color: #0f172a;
  letter-spacing: 1px;
  flex-shrink: 0;
}
.panel-title::before {
  content: '';
  width: 4px;
  height: 15px;
  border-radius: 2px;
  background: #0ea5e9;
}
.chart-box { flex: 1; min-height: 0; }

.panel-map { padding-bottom: 8px; }
.map-wrap {
  position: relative;
  flex: 1;
  min-height: 0;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}
.map-foot {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

/* ===== 子组件光明适配 ===== */
/* StatCard */
.screen :deep(.stat-card) {
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  border-radius: 10px;
}
.screen :deep(.stat-card .label) { color: #64748b; }
.screen :deep(.stat-card .value) { color: #0f172a !important; }
.screen :deep(.stat-card .suffix) { color: #94a3b8; }

/* EventTicker */
.screen :deep(.ticker-head) { border-bottom-color: #e2e8f0; }
.screen :deep(.ticker .live) { color: #475569; }
.screen :deep(.ticker .count) { color: #94a3b8; }
.screen :deep(.ticker .item) { border-bottom-color: #f1f5f9; }
.screen :deep(.ticker .msg) { color: #334155; }
.screen :deep(.ticker .time) { color: #94a3b8; }
.screen :deep(.ticker .empty) { color: #94a3b8; }

/* 高德地图容器：加载前/无瓦片时保持浅灰背景 */
.screen :deep(.amap-container) {
  background: #f8fafc;
}
.screen :deep(.ydr-legend) {
  background: rgba(255, 255, 255, 0.92) !important;
  color: #334155 !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 8px !important;
  padding: 8px 10px !important;
  font-size: 12px !important;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
}

@media (max-width: 1280px) {
  .kpi-row { grid-template-columns: repeat(3, 1fr); }
  .scr-body { grid-template-columns: 1fr; grid-auto-rows: minmax(280px, auto); overflow: auto; }
  .scr-side { min-width: 0; }
  .scr-title-main { font-size: 20px; }
}
</style>
