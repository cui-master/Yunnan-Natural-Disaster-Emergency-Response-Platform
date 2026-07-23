import request from './request'

/**
 * 图片/视频上传（转发到后端 /api/upload -> MinIO）。
 * 后端当前版本尚未提供该接口；VITE_USE_MOCK=true 时由 Mock 返回占位 URL。
 * 返回图片/视频 URL 数组，便于上报页直接拼装 images 字段。
 */
export async function uploadFiles(formData: FormData): Promise<string[]> {
  const r = await request.post<{ urls?: string[]; url?: string }>('/api/upload', formData)
  if (Array.isArray(r.urls)) return r.urls
  if (r.url) return [r.url]
  return []
}
