"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { RequireAuth } from "@/components/RequireAuth";
import { IncidentCard } from "@/components/IncidentCard";
import { useAuth } from "@/components/AuthProvider";
import { getIncidents } from "@/lib/api";
import { getRecentReports, type LocalReport } from "@/lib/storage";
import type { Incident } from "@/lib/types";

function ProfileInner() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [myReports, setMyReports] = useState<LocalReport[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);

  useEffect(() => {
    setMyReports(getRecentReports());
    let alive = true;
    getIncidents()
      .then((data) => {
        if (alive) setIncidents(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        if (alive) setIncidents([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="px-4 pt-4 pb-safe space-y-4">
      {/* 用户信息 */}
      <section className="rounded-3xl bg-gradient-to-br from-emergency-blue to-emergency-blue-dark p-5 text-white shadow-card">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-2xl">
            👤
          </div>
          <div className="min-w-0">
            <p className="text-lg font-bold truncate">
              {user?.realName || user?.username || "信息员"}
            </p>
            <p className="text-white/80 text-sm">
              {user?.roleName || user?.roleKey || "普通信息员"}
            </p>
            {user?.username && (
              <p className="text-white/60 text-xs mt-0.5">账号：{user.username}</p>
            )}
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="mt-4 w-full h-11 rounded-xl bg-white/15 backdrop-blur text-white font-medium active:bg-white/25"
        >
          退出登录
        </button>
      </section>

      {/* 我的上报（本地暂存） */}
      <section>
        <div className="flex items-center justify-between px-1 mb-2">
          <h3 className="font-semibold text-gray-800">我的上报</h3>
          <span className="text-xs text-gray-400">{myReports.length} 条</span>
        </div>
        {myReports.length === 0 ? (
          <div className="text-sm text-gray-400 py-8 text-center rounded-2xl bg-white shadow-card">
            还没有上报记录，去
            <Link href="/report" className="text-emergency-blue">
              我要上报
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {myReports.map((r) => (
              <IncidentCard
                key={r.id}
                item={{
                  id: r.id,
                  code: r.code,
                  title: r.title,
                  type: r.type,
                  level: r.level,
                  status: r.status,
                  createdAt: r.createdAt,
                }}
              />
            ))}
          </div>
        )}
      </section>

      {/* 近期灾情动态（兜底数据源 /api/incidents） */}
      <section>
        <div className="flex items-center justify-between px-1 mb-2">
          <h3 className="font-semibold text-gray-800">近期灾情动态</h3>
          <span className="text-xs text-gray-400">来自 /api/incidents</span>
        </div>
        {incidents.length === 0 ? (
          <div className="text-sm text-gray-400 py-8 text-center rounded-2xl bg-white shadow-card">
            暂无灾情动态
          </div>
        ) : (
          <div className="space-y-3">
            {incidents.slice(0, 8).map((item) => (
              <IncidentCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <RequireAuth>
      <ProfileInner />
    </RequireAuth>
  );
}
