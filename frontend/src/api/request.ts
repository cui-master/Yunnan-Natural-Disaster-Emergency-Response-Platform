import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { USE_MOCK, mockAdapter } from './mock'

// 与后端（Spring Boot）对齐：api 模块统一使用完整路径 /api/...。
// - Mock 模式：baseURL 置空，适配器直接按 /api/... 路由。
// - 真实模式：若 VITE_API_BASE 为 '/api' 或为空，则走同源 /api（由 Vite proxy / Nginx 转发到后端）；
//   若为完整地址（如 http://localhost:8080），则直接请求该地址。
const apiBase = import.meta.env.VITE_API_BASE || ''
const baseURL = USE_MOCK ? '' : apiBase === '/api' ? '' : apiBase

const http: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000
})

// 请求拦截：注入 JWT
http.interceptors.request.use((cfg) => {
  const t = localStorage.getItem('token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  if (USE_MOCK) cfg.headers['X-Mock'] = '1'
  return cfg
})

// 响应拦截：统一拆包 R<T> -> T（业务错误抛异常）
function unwrap(resp: AxiosResponse) {
  const body = resp.data
  if (body && typeof body === 'object' && 'code' in body) {
    if (body.code === 0 || body.code === 200) return body.data
    const err: any = new Error(body.message || '请求失败')
    err.business = true
    err.code = body.code
    throw err
  }
  return body
}

http.interceptors.response.use(unwrap as any, (err) => {
  if (err.response?.status === 401) {
    localStorage.removeItem('token')
    location.href = '/#/login'
  }
  return Promise.reject(err)
})

// 启用 Mock 联调层（前后端分离：VITE_USE_MOCK=true 时完全走本地适配器）
if (USE_MOCK) {
  ;(http.defaults as any).adapter = mockAdapter
}

// 类型安全的请求封装：返回 Promise<T>（已拆包）
export function get<T>(url: string, params?: any): Promise<T> {
  return http.get(url, { params }) as unknown as Promise<T>
}
export function post<T>(url: string, data?: any): Promise<T> {
  return http.post(url, data) as unknown as Promise<T>
}
export function put<T>(url: string, data?: any): Promise<T> {
  return http.put(url, data) as unknown as Promise<T>
}
export function del<T>(url: string): Promise<T> {
  return http.delete(url) as unknown as Promise<T>
}

export default { get, post, put, del }
export { http }
