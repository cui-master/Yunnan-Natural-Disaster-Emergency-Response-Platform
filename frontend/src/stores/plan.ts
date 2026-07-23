import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getPlans, getPlan, savePlan, approvePlan } from '@/api/plan'
import type { EmergencyPlan } from '@/types'

export const usePlanStore = defineStore('plan', () => {
  const list = ref<EmergencyPlan[]>([])
  const current = ref<EmergencyPlan | null>(null)
  const loading = ref(false)

  async function fetchList(eventId?: number) {
    loading.value = true
    try {
      const resp = await getPlans({ eventId })
      list.value = resp.list
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: number) {
    current.value = await getPlan(id)
    return current.value
  }

  async function save(id: number, data: Partial<EmergencyPlan>) {
    current.value = await savePlan(id, data)
    return current.value
  }

  async function approve(id: number) {
    current.value = await approvePlan(id)
    return current.value
  }

  return { list, current, loading, fetchList, fetchOne, save, approve }
})
