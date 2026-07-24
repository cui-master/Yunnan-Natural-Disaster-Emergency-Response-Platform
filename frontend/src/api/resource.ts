import request from './request'
import type { RescueResource, ResourceType, ResourceStatus, DispatchRecord, DispatchReq } from '@/types'

interface ResourceDTO {
  id: number
  name: string
  type: string
  total?: number
  available?: number
  unit?: string
  status: string
}

interface DispatchOrderDTO {
  id: number
  resourceId: number
  quantity?: number
  status: string
}

function toResource(d: ResourceDTO): RescueResource {
  return {
    id: d.id,
    name: d.name,
    type: (d.type || 'TEAM') as ResourceType,
    status: (d.status || 'IDLE') as ResourceStatus,
    city: '',
    location: '',
    capacity: d.total,
    owner: '',
    contact: '',
    updatedAt: ''
  }
}

function toDispatch(d: DispatchOrderDTO, eventId = 0): DispatchRecord {
  return {
    id: d.id,
    eventId,
    eventCode: '',
    resourceId: d.resourceId,
    resourceName: '',
    resourceType: 'TEAM',
    fromCity: '',
    toCity: '',
    toLocation: '',
    status: d.status,
    dispatchedBy: '',
    dispatchedAt: '',
    conflict: false
  }
}

export async function getResources(params: { type?: ResourceType; status?: ResourceStatus; city?: string; keyword?: string } = {}) {
  const list = await request.get<ResourceDTO[]>('/api/resources', params)
  return { list: list.map(toResource), total: list.length }
}

export function getResource(id: number) {
  return request.get<ResourceDTO>('/api/resources/' + id).then(toResource)
}

export function createResource(data: any) {
  return request.post<ResourceDTO>('/api/resources', data).then(toResource)
}

export function updateResource(id: number, data: any) {
  return request.put<ResourceDTO>('/api/resources/' + id, data).then(toResource)
}

export async function getDispatches(incidentId?: number) {
  const list = await request.get<DispatchOrderDTO[]>('/api/dispatch', { incidentId })
  return { list: list.map((d) => toDispatch(d, incidentId)), total: list.length }
}

export async function dispatchResources(data: DispatchReq) {
  const body = {
    incidentId: data.eventId,
    items: (data.resourceIds || []).map((rid) => ({ resourceId: rid, quantity: 1 }))
  }
  const list = await request.post<DispatchOrderDTO[]>('/api/dispatch', body)
  return { records: list.map((d) => toDispatch(d, data.eventId)), conflict: list.some((d) => d.status === 'CONFLICT') }
}

export function cancelDispatch(id: number) {
  return request.post<DispatchOrderDTO>('/api/dispatches/' + id + '/cancel').then((d) => toDispatch(d))
}
