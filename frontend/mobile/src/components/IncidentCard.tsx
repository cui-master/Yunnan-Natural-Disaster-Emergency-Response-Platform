"use client";

import { getDisasterType, getLevel, getStatus } from "@/lib/constants";
import type { Incident } from "@/lib/types";

function formatTime(ts?: string): string {
  if (!ts) return "";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  const pad = (n: number) => `${n}`.padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

// 灾情卡片（用于首页"最近灾情"与"我的上报"）
export function IncidentCard({ item }: { item: Incident }) {
  const type = getDisasterType(item.type);
  const level = getLevel(item.level);
  const status = getStatus(item.status);

  return (
    <div className="bg-white rounded-2xl shadow-card p-4 flex gap-3 active:scale-[0.99] transition">
      <div
        className={`shrink-0 w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${
          type?.badge ?? "bg-gray-100 text-gray-600"
        }`}
      >
        {type?.icon ?? "📍"}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <h4 className="font-semibold text-gray-800 truncate">
            {item.title || "未命名灾情"}
          </h4>
          <span
            className={`shrink-0 text-xs px-2 py-0.5 rounded-full ${status.badge}`}
          >
            {status.label}
          </span>
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500">
          <span className="px-2 py-0.5 rounded-full bg-gray-100">
            {type?.label ?? item.type}
          </span>
          {level && (
            <span className={`px-2 py-0.5 rounded-full ${level.badge}`}>
              {level.roman}
            </span>
          )}
          {item.code && <span className="text-gray-400">{item.code}</span>}
        </div>
        {item.locationText && (
          <p className="mt-1.5 text-xs text-gray-500 truncate">
            📍 {item.locationText}
          </p>
        )}
        {item.createdAt && (
          <p className="mt-1 text-xs text-gray-400">{formatTime(item.createdAt)}</p>
        )}
      </div>
    </div>
  );
}
