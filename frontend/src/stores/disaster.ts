import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getDisasters,
  getDashboardStat,
  getTypeCount,
  getCityCount,
  getTrend,
  createDisaster,
  reviewDisaster
} from '@/api/disaster'
import type { DisasterEvent, EventStatus, ReviewReq } from '@/types'

export const useDisasterStore = defineStore('disaster', () => {
  const list = ref<DisasterEvent[]>([])
  const total = ref(0)
  const loading = ref(false)
  const stat = ref<any>(null)
  const typeCount = ref<any[]>([])
  const cityCount = ref<any[]>([])
  const trend = ref<any[]>([])

  async function fetchList(params: Record<string, unknown> = {}) {
    loading.value = true
    try {
      const resp = await getDisasters(params as any)
      list.value = resp.list
      total.value = resp.total
    } finally {
      loading.value = false
    }
  }

  async function fetchStat() {
    stat.value = await getDashboardStat()
    typeCount.value = await getTypeCount()
    cityCount.value = await getCityCount()
    trend.value = await getTrend()
  }

  async function report(data: Parameters<typeof createDisaster>[0]) {
    return await createDisaster(data)
  }

  async function review(data: ReviewReq) {
    return await reviewDisaster(data)
  }

  const statusMeta: Record<EventStatus, { label: string; type: string }> = {
    PENDING_VERIFY: { label: '待核验', type: 'info' },
    CONFIRMED: { label: '已确认', type: 'warning' },
    IN_PROGRESS: { label: '处置中', type: 'primary' },
    CLOSED: { label: '已结束', type: 'success' },
    REJECTED: { label: '已驳回', type: 'danger' }
  }

  return { list, total, loading, stat, typeCount, cityCount, trend, fetchList, fetchStat, report, review, statusMeta }
})
