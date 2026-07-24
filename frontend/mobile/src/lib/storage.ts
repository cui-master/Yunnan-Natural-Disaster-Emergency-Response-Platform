import type { LoginResult } from "./types";

const TOKEN_KEY = "yn_token";
const USER_KEY = "yn_user";
const RECENT_REPORTS_KEY = "yn_recent_reports";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

// ---- Token ----
export function getToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (!isBrowser()) return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(TOKEN_KEY);
}

// ---- User ----
export function getUser(): LoginResult | null {
  if (!isBrowser()) return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as LoginResult) : null;
  } catch {
    return null;
  }
}

export function setUser(user: LoginResult): void {
  if (!isBrowser()) return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearUser(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(USER_KEY);
}

// ---- 最近上报（本地暂存，用于"我的上报"） ----
export interface LocalReport {
  id: string | number;
  code?: string;
  title: string;
  type: string;
  level: string;
  status: string;
  createdAt: string;
}

export function getRecentReports(): LocalReport[] {
  if (!isBrowser()) return [];
  try {
    const raw = localStorage.getItem(RECENT_REPORTS_KEY);
    return raw ? (JSON.parse(raw) as LocalReport[]) : [];
  } catch {
    return [];
  }
}

export function addRecentReport(report: LocalReport): void {
  if (!isBrowser()) return;
  const list = getRecentReports();
  list.unshift(report);
  localStorage.setItem(RECENT_REPORTS_KEY, JSON.stringify(list.slice(0, 30)));
}

// ---- 上报草稿（自动保存，避免误退出丢失） ----
const DRAFT_KEY = "yn_report_draft";

export interface ReportDraft {
  title: string;
  type: string;
  level: string;
  content: string;
  locationText: string;
  contact: string;
  images: string;
  savedAt: number;
}

export function getDraft(): ReportDraft | null {
  if (!isBrowser()) return null;
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    return raw ? (JSON.parse(raw) as ReportDraft) : null;
  } catch {
    return null;
  }
}

export function setDraft(draft: Omit<ReportDraft, "savedAt">): void {
  if (!isBrowser()) return;
  localStorage.setItem(DRAFT_KEY, JSON.stringify({ ...draft, savedAt: Date.now() }));
}

export function clearDraft(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(DRAFT_KEY);
}
