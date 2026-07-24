import { get, post, del } from './request'
import { USE_MOCK } from './mock'
import type { KnowledgeKitDoc, KnowledgeKitUploadResp } from '@/types'

// 知识库（Dify）接口：前端 → Spring Boot 桥接(/api/knowledge/*) → FastAPI ai_service → Dify
// 仅传知识库中文名(kbName)，dataset_id 与密钥在 ai_service 侧维护。

export function listKnowledgeKitDocs(kbName: string) {
  return get<{ list: KnowledgeKitDoc[]; total: number }>('/api/knowledge/documents', {
    params: { kbName }
  })
}

export function deleteKnowledgeKitDoc(kbName: string, docId: string) {
  return del<boolean>(
    `/api/knowledge/documents/${encodeURIComponent(docId)}?kbName=${encodeURIComponent(kbName)}`
  )
}

// 知识库注册表（DB 为唯一真源）：前端下拉从这里拉，落库后展示 dataset_id
export function listKnowledgeBases() {
  return get<
    Array<{ kbKey: string; kbName: string; datasetId: string; description: string }>
  >('/api/knowledge/bases')
}

// 上传：mock 走 axios 适配器；真实后端走 XHR 以支持进度条
// 注意：kbName 放在 URL 查询参数（非 multipart 字段），避免 Tomcat 对多部件中文按 ISO-8859-1 解码乱码
export function uploadKnowledgeKit(
  kbName: string,
  files: File[],
  onProgress?: (p: number) => void
): Promise<KnowledgeKitUploadResp> {
  const buildForm = () => {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    return form
  }

  if (USE_MOCK) {
    return post<KnowledgeKitUploadResp>(
      '/api/knowledge/upload?kbName=' + encodeURIComponent(kbName),
      buildForm()
    )
  }

  const base = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
  const url = base + '/api/knowledge/upload?kbName=' + encodeURIComponent(kbName)
  const token = localStorage.getItem('token') || ''
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', url)
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    }
    xhr.onload = () => {
      try {
        const body = JSON.parse(xhr.responseText)
        if (body && 'code' in body) {
          if (body.code === 0 || body.code === 200) resolve(body.data)
          else reject(new Error(body.message || '上传失败'))
        } else resolve(body)
      } catch (err) {
        reject(err)
      }
    }
    xhr.onerror = () => reject(new Error('网络错误'))
    xhr.send(buildForm())
  })
}
