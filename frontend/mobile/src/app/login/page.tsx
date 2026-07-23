"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { DEMO_ACCOUNT } from "@/lib/constants";
import { useToast } from "@/components/ToastProvider";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { toast } = useToast();
  const [username, setUsername] = useState(DEMO_ACCOUNT.username);
  const [password, setPassword] = useState(DEMO_ACCOUNT.password);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      toast("请输入用户名和密码", "error");
      return;
    }
    setLoading(true);
    try {
      await login(username.trim(), password);
      toast("登录成功", "success");
      router.replace("/");
    } catch (err) {
      toast(err instanceof Error ? err.message : "登录失败", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-emergency-blue to-emergency-blue-dark px-6 pb-safe">
      <div className="flex-1 flex flex-col items-center justify-center">
        <div className="w-16 h-16 rounded-2xl bg-white/15 backdrop-blur flex items-center justify-center text-3xl mb-4">
          🛡️
        </div>
        <h1 className="text-white text-2xl font-bold tracking-wide">
          云南自然灾害应急
        </h1>
        <p className="text-white/80 text-sm mt-1">信息员移动工作端</p>

        <form
          onSubmit={handleSubmit}
          className="mt-10 w-full max-w-sm bg-white rounded-3xl shadow-card p-6 space-y-4"
        >
          <div>
            <label className="block text-sm text-gray-600 mb-1.5">用户名</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              autoComplete="username"
              className="w-full h-12 px-4 rounded-xl bg-gray-50 border border-gray-200 text-gray-800 outline-none focus:border-emergency-blue"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1.5">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              autoComplete="current-password"
              className="w-full h-12 px-4 rounded-xl bg-gray-50 border border-gray-200 text-gray-800 outline-none focus:border-emergency-blue"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full h-12 rounded-xl bg-emergency-blue text-white font-semibold text-base active:bg-emergency-blue-dark disabled:opacity-60"
          >
            {loading ? "登录中…" : "登 录"}
          </button>
          <p className="text-xs text-gray-400 text-center">
            演示账号：{DEMO_ACCOUNT.username} / {DEMO_ACCOUNT.password}
          </p>
        </form>
      </div>
    </div>
  );
}
