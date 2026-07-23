import request from './request'
import type { KnowledgeDoc, KnowledgeCategory, KnowledgeUploadReq, AuditLog, SystemUser, SystemConfig } from '@/types'

// 注：知识库 / 审计日志 / 系统管理 为前端页面，后端当前版本尚未提供对应接口。
// 前后端分离：VITE_USE_MOCK=true 时由 Mock 层返回；置为 false 时需后端补充这些接口。

export function getKnowledge(params: { category?: KnowledgeCategory; keyword?: string } = {}) {
  return request.get<{ list: KnowledgeDoc[]; total: number }>('/api/knowledge', params)
}
export function uploadKnowledge(data: KnowledgeUploadReq) {
  return request.post<KnowledgeDoc>('/api/knowledge', data)
}
export function deleteKnowledge(id: number) {
  return request.del<boolean>('/api/knowledge/' + id)
}
export function getAuditLogs(params: { keyword?: string; page?: number; pageSize?: number } = {}) {
  return request.get<{ list: AuditLog[]; total: number }>('/api/audit/logs', params)
}
export function getSystemUsers() {
  return request.get<{ list: SystemUser[]; total: number }>('/api/system/users')
}
export function createSystemUser(data: any) {
  return request.post<unknown>('/api/system/users', data)
}
export function updateSystemUser(id: number, data: any) {
  return request.put<unknown>('/api/system/users/' + id, data)
}
export function getRoles() {
  return request.get<unknown>('/api/system/roles')
}
export function getSystemConfig() {
  return request.get<SystemConfig[]>('/api/system/config')
}
export function updateSystemConfig(data: any) {
  return request.put<unknown>('/api/system/config', data)
}
