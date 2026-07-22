import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getKnowledge, uploadKnowledge, deleteKnowledge } from '@/api/system'
import type { KnowledgeDoc, KnowledgeUploadReq } from '@/types'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const docs = ref<KnowledgeDoc[]>([])
  const loading = ref(false)

  async function fetchDocs(params: Record<string, unknown> = {}) {
    loading.value = true
    try {
      const resp = await getKnowledge(params as any)
      docs.value = resp.list
    } finally {
      loading.value = false
    }
  }

  async function upload(data: KnowledgeUploadReq) {
    return await uploadKnowledge(data)
  }

  async function remove(id: number) {
    return await deleteKnowledge(id)
  }

  return { docs, loading, fetchDocs, upload, remove }
})
