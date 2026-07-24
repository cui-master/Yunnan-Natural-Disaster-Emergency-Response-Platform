import request, { http } from './request'
import { USE_MOCK, simulatePlanStream } from './mock'
import type { EmergencyPlan, PlanGenerateReq, PlanStreamChunk } from '@/types'

// 后端 EmergencyPlan DTO
interface PlanDTO {
  id: number
  incidentId?: number
  title?: string
  content?: string // JSON 字符串，结构见 AiPlan
  status?: string
  createdAt?: string
  updatedAt?: string
}

interface AiPlan {
  title?: string
  sections?: { title: string; content: string }[]
  references?: { docId: number; docTitle: string; snippet: string; score: number }[]
  compliance?: { passed: boolean; score: number; issues: string[]; suggestions: string[] }
}

function toPlan(d: PlanDTO): EmergencyPlan {
  let ai: AiPlan = {}
  try {
    ai = d.content ? JSON.parse(d.content) : {}
  } catch {
    ai = { sections: [{ title: d.title || '处置方案', content: d.content || '' }] }
  }
  return {
    id: d.id,
    eventId: d.incidentId || 0,
    eventCode: '',
    title: ai.title || d.title || '应急响应方案',
    level: 'III',
    type: 'EARTHQUAKE',
    status: (d.status as EmergencyPlan['status']) || 'DRAFT',
    sections: ai.sections || [],
    references: ai.references || [],
    compliance: ai.compliance,
    createdBy: '',
    createdAt: d.createdAt || '',
    updatedAt: d.updatedAt || ''
  }
}

export function getPlans(_params: { eventId?: number } = {}) {
  // 后端仅按 id 查单方案；列表由前端维护。这里返回空列表占位。
  return Promise.resolve({ list: [] as EmergencyPlan[], total: 0 })
}

export async function getPlan(id: number) {
  const d = await request.get<PlanDTO>('/api/plans/' + id)
  return toPlan(d)
}

export async function savePlan(id: number, data: Partial<EmergencyPlan>) {
  const body = {
    title: data.title,
    content: JSON.stringify({
      title: data.title,
      sections: data.sections,
      references: data.references,
      compliance: data.compliance
    }),
    status: data.status
  }
  const d = await request.put<PlanDTO>('/api/plans/' + id, body)
  return toPlan(d)
}

export async function approvePlan(id: number, content?: string) {
  const d = await request.post<PlanDTO>('/api/plans/' + id + '/approve', { content: content || '' })
  return toPlan(d)
}

/**
 * 流式生成应急方案。
 * - Mock 模式：本地模拟器逐块回调。
 * - 真实模式：连接后端 SSE（GET /api/incidents/{id}/plan），把 progress/done 事件翻译为前端 chunk。
 */
export function generatePlanStream(
  data: PlanGenerateReq,
  onChunk: (chunk: PlanStreamChunk) => void,
  onError?: (e: unknown) => void
): () => void {
  if (USE_MOCK) {
    return simulatePlanStream(data.eventId, onChunk as (c: any) => void, data.extraRequirement)
  }
<<<<<<< HEAD
  // EventSource 无法设置 Authorization header，token 通过 query 参数传递（后端 JwtFilter 会兜底读取）
  const token = localStorage.getItem('token') || ''
  const es = new EventSource('/api/incidents/' + data.eventId + '/plan?token=' + encodeURIComponent(token))
=======
  const es = new EventSource('/api/incidents/' + data.eventId + '/plan')
>>>>>>> feature-cui
  es.addEventListener('progress', (ev: MessageEvent) => {
    onChunk({ type: 'SECTION', title: ev.data })
  })
  es.addEventListener('done', async (ev: MessageEvent) => {
    const planId = Number(ev.data)
    onChunk({ type: 'START', planId })
    try {
      const plan = await getPlan(planId)
      plan.sections.forEach((s) => onChunk({ type: 'SECTION', title: s.title }))
      plan.references.forEach((r) => onChunk({ type: 'REFERENCE', reference: r }))
      if (plan.compliance) onChunk({ type: 'COMPLIANCE', compliance: plan.compliance })
    } catch {
      /* ignore */
    }
    onChunk({ type: 'DONE', planId })
    es.close()
  })
  es.addEventListener('error', () => {
    onError?.(new Error('方案生成连接异常'))
    es.close()
  })
  return () => es.close()
}
