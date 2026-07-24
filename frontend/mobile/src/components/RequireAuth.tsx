"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./AuthProvider";

// 路由守卫：未登录则跳转登录页；登录中显示加载态
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !token) {
      router.replace("/login");
    }
  }, [loading, token, router]);

  if (loading || !token) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-gray-400 text-sm">
        加载中…
      </div>
    );
  }
  return <>{children}</>;
}
