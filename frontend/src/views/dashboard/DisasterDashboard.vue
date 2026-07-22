<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useDisasterStore } from '@/stores/disaster'
import { useAuthStore } from '@/stores/auth'
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
    pushRealtime({
      id: rid++,
      eventId: d.id,
      eventCode: d.code,
      type: m.type,
      message: m.msg(d),
      status: d.status as any,
      createdAt: new Date().toISOString()
    })
  }, 4500)
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

// 图表配置
const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, type: 'scroll' },
  series: [
    {
      type: 'pie',
      radius: ['40%', '68%'],
      center: ['50%', '45%'],
      data: typeCount.value.map((t) => ({ name: typeLabel[t.type] || t.type, value: t.count })),
      label: { show: false }
    }
  ]
}))

const barOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 60, right: 20, top: 20, bottom: 50 },
  xAxis: { type: 'category', data: cityCount.value.map((c) => c.city), axisLabel: { interval: 0, rotate: 35, fontSize: 10 } },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: cityCount.value.map((c) => c.count), itemStyle: { color: '#c0392b', borderRadius: [4, 4, 0, 0] } }]
}))

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 20, bottom: 30 },
  xAxis: { type: 'category', data: trend.value.map((t) => t.date) },
  yAxis: { type: 'value' },
  series: [{ type: 'line', smooth: true, data: trend.value.map((t) => t.count), areaStyle: { opacity: 0.15 }, itemStyle: { color: '#2980b9' } }]
}))

onMounted(async () => {
  await disaster.fetchStat()
  await disaster.fetchList({ pageSize: 100 })
  if (USE_MOCK) startMockFeed()
  else startRealFeed()
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  ws?.close()
})
</script>

<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats">
      <StatCard title="灾情总数" :value="stat?.eventTotal ?? 0" icon="Warning" color="#c0392b" />
      <StatCard title="处置中" :value="stat?.handlingCount ?? 0" icon="Loading" color="#e67e22" />
      <StatCard title="待核验" :value="stat?.pendingVerifyCount ?? 0" icon="Bell" color="#f1c40f" />
      <StatCard title="受影响人口" :value="(stat?.affectedPopulation ?? 0).toLocaleString()" icon="User" color="#2980b9" />
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
  gap: 14px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
}
.grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 14px;
}
.grid.charts {
  grid-template-columns: repeat(3, 1fr);
}
.panel {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
}
.panel-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #1f2d3d;
}
.map-wrap {
  flex: 1;
  min-height: 420px;
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
</style>
