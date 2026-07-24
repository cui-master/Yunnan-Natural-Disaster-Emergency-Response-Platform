import request from './request'
import type { LoginReq, LoginResp } from '@/types'

export function login(data: LoginReq) {
  return request.post<LoginResp>('/api/auth/login', data)
}

export function me() {
  return request.get<LoginResp>('/api/auth/me')
}
