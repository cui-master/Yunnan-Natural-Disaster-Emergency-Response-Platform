"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { RequireAuth } from "@/components/RequireAuth";
import { IncidentCard } from "@/components/IncidentCard";
import { getIncidents } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import type { Incident } from "@/lib/types";

function HomeInner() {
  const { user } = useAuth();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    getIncidents()
      .then((data) => {
        if (alive) setIncidents(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        if (alive) setIncidents([]);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="px-4 pt-4 pb-safe space-y-4">
      {/* 速览 + 我要上报 */}
      <section className="rounded-3xl bg-gradient-to-br from-emergency-blue to-emergency-blue-dark p-5 text-white shadow-card">
        <p className="text-white/80 text-sm">
          您好，{user?.realName || user?.username || "信息员"}
        </p>
        <h2 className="text-xl font-bold mt-1">发现灾情？立即上报</h2>
        <p className="text-white/75 text-sm mt-1">
          作为一线信息员，您的及时报送是应急救援的第一手依据。
        </p>
        <Link
          href="/report"
          className="mt-4 inline-flex items-center justify-center w-full h-12 rounded-xl bg-white text-emergency-blue font-semibold active:scale-[0.99] transition"
        >
          ＋ 我要上报灾情
        </Link>
      </section>

      {/* 最近灾情 */}
      <section>
        <div className="flex items-center justify-between px-1 mb-2">
          <h3 className="font-semibold text-gray-800">最近灾情</h3>
          <span className="text-xs text-gray-400">来自 /api/incidents</span>
        </div>
        {loading ? (
          <div className="text-sm text-gray-400 py-8 text-center">加载中…</div>
        ) : incidents.length === 0 ? (
          <div className="text-sm text-gray-400 py-8 text-center rounded-2xl bg-white shadow-card">
            暂无灾情动态
          </div>
        ) : (
          <div className="space-y-3">
            {incidents.slice(0, 10).map((item) => (
              <IncidentCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default function HomePage() {
  return (
    <RequireAuth>
      <HomeInner />
    </RequireAuth>
  );
}
