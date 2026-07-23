// 统一响应结构：{ code, message, data }，code===0 成功
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

// 登录 / 当前用户信息
export interface LoginResult {
  token: string;
  username: string;
  realName: string;
  roleKey: string;
  roleName: string;
}

// 上报灾情请求体（字段名严格对齐后端契约）
export interface ReportPayload {
  title: string;
  type: string; // EARTHQUAKE / FLOOD / ...
  level: string; // I / II / III / IV
  content: string;
  locationText: string;
  lat: number;
  lng: number;
  images: string; // 逗号分隔的 URL 字符串（不是数组）
  contact: string;
}

// 上报成功后返回的记录对象（含 id、status 等）
export interface ReportRecord {
  id: string | number;
  code?: string;
  title: string;
  type: string;
  level: string;
  status?: string;
  createdAt?: string;
  [key: string]: unknown;
}

// 灾情事件（/api/incidents 兜底列表）
export interface Incident {
  id: string | number;
  code?: string;
  title: string;
  type: string;
  level: string;
  status: string;
  createdAt?: string;
  locationText?: string;
  [key: string]: unknown;
}

// 上传返回
export interface UploadResult {
  url: string;
}
