import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listKnowledgeKitDocs, uploadKnowledgeKit, deleteKnowledgeKitDoc } from '@/api/knowledgeKit'
import type { KnowledgeKitDoc } from '@/types'

export const useKnowledgeKitStore = defineStore('knowledgeKit', () => {
  const docs = ref<KnowledgeKitDoc[]>([])
  const loading = ref(false)
  const uploading = ref(false)
  const progress = ref(0)

  async function fetchDocs(kbName: string) {
    loading.value = true
    try {
      const resp = await listKnowledgeKitDocs(kbName)
      docs.value = resp.list
    } finally {
      loading.value = false
    }
  }

  async function upload(kbName: string, files: File[]) {
    uploading.value = true
    progress.value = 0
    try {
      const r = await uploadKnowledgeKit(kbName, files, (p) => (progress.value = p))
      return r
    } finally {
      uploading.value = false
      progress.value = 0
    }
  }

  async function remove(kbName: string, docId: string) {
    return await deleteKnowledgeKitDoc(kbName, docId)
  }

  return { docs, loading, uploading, progress, fetchDocs, upload, remove }
})
