import type {
  ApiResponse,
  Incident,
  LoginResult,
  ReportPayload,
  ReportRecord,
  UploadResult,
} from "./types";
import { getToken } from "./storage";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080").replace(
  /\/+$/,
  ""
);

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    throw new Error(`网络错误 HTTP ${res.status}`);
  }
  const json = (await res.json()) as ApiResponse<T>;
  if (json.code !== 0) {
    throw new Error(json.message || "请求失败");
  }
  return json.data;
}

// 1. 登录
export function login(
  username: string,
  password: string
): Promise<LoginResult> {
  return request<LoginResult>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

// 2. 当前用户
export function getMe(): Promise<LoginResult> {
  return request<LoginResult>("/api/auth/me", { method: "GET" });
}

// 3. 上报灾情
export function submitReport(payload: ReportPayload): Promise<ReportRecord> {
  return request<ReportRecord>("/api/reports", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// 4. 文件上传（multipart/form-data，字段名 file）
export async function uploadFile(file: File): Promise<string> {
  return uploadWithProgress(file);
}

// 带进度回调的上传（使用 XHR 以便监听 upload.onprogress）
export function uploadWithProgress(
  file: File,
  onProgress?: (percent: number) => void
): Promise<string> {
  const token = getToken();
  return new Promise<string>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const form = new FormData();
    form.append("file", file);

    xhr.open("POST", `${API_BASE}/api/upload`);
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const json = JSON.parse(xhr.responseText) as ApiResponse<UploadResult>;
          if (json.code !== 0) {
            reject(new Error(json.message || "上传失败"));
            return;
          }
          resolve(json.data.url);
        } catch {
          reject(new Error("上传响应解析失败"));
        }
      } else {
        reject(new Error(`上传失败 HTTP ${xhr.status}`));
      }
    };
    xhr.onerror = () => reject(new Error("网络错误，上传失败"));
    xhr.send(form);
  });
}

// 5. 灾情列表（兜底展示）
export function getIncidents(): Promise<Incident[]> {
  return request<Incident[]>("/api/incidents", { method: "GET" });
}

export { API_BASE };
