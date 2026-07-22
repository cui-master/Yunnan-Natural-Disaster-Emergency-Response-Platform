import request from './request'
import type {
  DisasterEvent,
  DisasterReportReq,
  DisasterType,
  EventStatus,
  ReviewReq,
  DashboardStat,
  TypeCount,
  CityCount,
  TrendPoint
} from '@/types'

// 后端 Incident DTO
interface IncidentDTO {
  id: number
  code?: string
  title?: string
  type: string
  level: string
  status: string
  description?: string
  locationText?: string
  lat?: number
  lng?: number
  images?: string
  contact?: string
  reporterName?: string
  createdAt?: string
  updatedAt?: string
}

interface ResourceDTO {
  id: number
  name: string
  type: string
  total?: number
  available?: number
  unit?: string
  status: string
}

function toEvent(d: IncidentDTO): DisasterEvent {
  return {
    id: d.id,
    code: d.code || 'YN-' + d.id,
    title: d.title || d.locationText || '未命名灾情',
    type: (d.type || 'EARTHQUAKE') as DisasterEvent['type'],
    level: (d.level || 'IV') as DisasterEvent['level'],
    status: (d.status || 'PENDING_VERIFY') as EventStatus,
    province: '云南省',
    city: d.locationText || '',
    district: '',
    location: d.locationText || '',
    geo: { lng: Number(d.lng) || 0, lat: Number(d.lat) || 0 },
    description: d.description || '',
    reporter: d.reporterName || '一线信息员',
    images: d.images ? d.images.split(',').filter(Boolean) : [],
    createdAt: d.createdAt || '',
    updatedAt: d.updatedAt || ''
  }
}

export async function getDisasters(params: { status?: string; type?: string; pageSize?: number } = {}) {
  const list = await request.get<IncidentDTO[]>('/api/incidents', params)
  return { list: list.map(toEvent), total: list.length }
}

// 大屏统计：后端无统计接口，由 /api/incidents + /api/resources 客户端聚合（前后端分离，无需额外后端开发）
export async function getDashboardStat(): Promise<DashboardStat> {
  const [incidents, resources] = await Promise.all([
    request.get<IncidentDTO[]>('/api/incidents'),
    request.get<ResourceDTO[]>('/api/resources').catch(() => [] as ResourceDTO[])
  ])
  return {
    eventTotal: incidents.length,
    handlingCount: incidents.filter((d) => d.status === 'IN_PROGRESS').length,
    pendingVerifyCount: incidents.filter((d) => d.status === 'PENDING_VERIFY').length,
    finishedCount: incidents.filter((d) => d.status === 'CLOSED').length,
    resourceTotal: resources.length,
    resourceIdle: resources.filter((r) => r.status === 'IDLE').length,
    affectedPopulation: incidents.reduce((s, d) => s + (Number((d as any).affectedPopulation) || 0), 0),
    casualties: incidents.reduce((s, d) => s + (Number((d as any).casualties) || 0), 0)
  }
}

export async function getTypeCount(): Promise<TypeCount[]> {
  const list = await request.get<IncidentDTO[]>('/api/incidents')
  const map: Record<string, number> = {}
  list.forEach((d) => (map[d.type] = (map[d.type] || 0) + 1))
  return Object.entries(map).map(([type, count]) => ({ type: type as DisasterType, count }))
}
export async function getCityCount(): Promise<CityCount[]> {
  const list = await request.get<IncidentDTO[]>('/api/incidents')
  const map: Record<string, number> = {}
  list.forEach((d) => {
    const c = d.locationText || '未知'
    map[c] = (map[c] || 0) + 1
  })
  return Object.entries(map).map(([city, count]) => ({ city, count }))
}
export async function getTrend(): Promise<TrendPoint[]> {
  const list = await request.get<IncidentDTO[]>('/api/incidents')
  const map: Record<string, number> = {}
  list.forEach((d) => {
    const day = (d.createdAt || '').slice(0, 10)
    if (day) map[day] = (map[day] || 0) + 1
  })
  return Object.entries(map)
    .map(([date, count]) => ({ date, count }))
    .sort((a, b) => a.date.localeCompare(b.date))
}

export async function createDisaster(data: DisasterReportReq): Promise<DisasterEvent> {
  const body = {
    title: data.title,
    type: data.type,
    level: data.level,
    content: data.description,
    locationText: [data.city, data.district, data.location].filter(Boolean).join(''),
    lat: data.lat,
    lng: data.lng,
    images: data.images.join(','),
    contact: ''
  }
  const d = await request.post<IncidentDTO>('/api/reports', body)
  return toEvent(d)
}

export async function reviewDisaster(data: ReviewReq): Promise<DisasterEvent> {
  const map: Record<string, string> = {
    CONFIRM: '/confirm',
    REJECT: '/reject',
    CLOSE: '/close'
  }
  const d = await request.post<IncidentDTO>(`/api/incidents/${data.eventId}${map[data.action]}`)
  return toEvent(d)
}
