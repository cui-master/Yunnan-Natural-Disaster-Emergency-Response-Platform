import api from './request'
import type { LoginResp, Incident, Resource, EmergencyPlan, DispatchOrder } from '../types'

// 后端统一返回 R<T> = { code, message, data }，此处解包出 data
export const login = (username: string, password: string) =>
  api.post<LoginResp>('/auth/login', { username, password }).then((r) => r.data.data)

export const me = () => api.get<LoginResp>('/auth/me').then((r) => r.data.data)

export const submitReport = (data: any) => api.post('/reports', data).then((r) => r.data.data)

export const listIncidents = (status?: string, type?: string) =>
  api.get<Incident[]>('/incidents', { params: { status, type } }).then((r) => r.data.data)

export const confirmIncident = (id: number) =>
  api.post(`/incidents/${id}/confirm`).then((r) => r.data.data)

export const rejectIncident = (id: number) =>
  api.post(`/incidents/${id}/reject`).then((r) => r.data.data)

export const closeIncident = (id: number) =>
  api.post(`/incidents/${id}/close`).then((r) => r.data.data)

export const listResources = () => api.get<Resource[]>('/resources').then((r) => r.data.data)

export const createResource = (data: any) => api.post('/resources', data).then((r) => r.data.data)

export const updateResource = (id: number, data: any) =>
  api.put(`/resources/${id}`, data).then((r) => r.data.data)

export const approvePlan = (id: number, content: string) =>
  api.post(`/plans/${id}/approve`, { content }).then((r) => r.data.data)

export const getPlan = (id: number) =>
  api.get<EmergencyPlan>(`/plans/${id}`).then((r) => r.data.data)

export const createDispatch = (data: any) => api.post('/dispatch', data).then((r) => r.data.data)

export const listDispatch = (incidentId: number) =>
  api.get<DispatchOrder[]>('/dispatch', { params: { incidentId } }).then((r) => r.data.data)
