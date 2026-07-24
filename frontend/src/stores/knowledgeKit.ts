import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  listKnowledgeKitDocs,
  uploadKnowledgeKit,
  deleteKnowledgeKitDoc,
  listKnowledgeBases
} from '@/api/knowledgeKit'
import type { KnowledgeKitDoc } from '@/types'

export interface KnowledgeBaseMeta {
  kbKey: string
  kbName: string
  datasetId: string
  description: string
}

export const useKnowledgeKitStore = defineStore('knowledgeKit', () => {
  const docs = ref<KnowledgeKitDoc[]>([])
  const loading = ref(false)
  const uploading = ref(false)
  const progress = ref(0)
  const bases = ref<KnowledgeBaseMeta[]>([])

  async function fetchBases() {
    try {
      bases.value = await listKnowledgeBases()
    } catch {
      bases.value = []
    }
  }

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

  return { docs, loading, uploading, progress, bases, fetchBases, fetchDocs, upload, remove }
})
