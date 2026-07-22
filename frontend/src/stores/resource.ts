import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getResources, getDispatches, dispatchResources, cancelDispatch } from '@/api/resource'
import type { RescueResource, DispatchRecord, DispatchReq } from '@/types'

export const useResourceStore = defineStore('resource', () => {
  const resources = ref<RescueResource[]>([])
  const dispatches = ref<DispatchRecord[]>([])
  const loading = ref(false)

  async function fetchResources(params: Record<string, unknown> = {}) {
    loading.value = true
    try {
      const resp = await getResources(params as any)
      resources.value = resp.list
    } finally {
      loading.value = false
    }
  }

  async function fetchDispatches() {
    const resp = await getDispatches()
    dispatches.value = resp.list
  }

  async function dispatch(data: DispatchReq) {
    return await dispatchResources(data)
  }

  async function cancel(id: number) {
    return await cancelDispatch(id)
  }

  return { resources, dispatches, loading, fetchResources, fetchDispatches, dispatch, cancel }
})
