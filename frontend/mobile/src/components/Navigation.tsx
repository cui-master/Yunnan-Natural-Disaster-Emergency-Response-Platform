"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "./AuthProvider";

function TabIcon({ name, active }: { name: string; active: boolean }) {
  const cls = active ? "text-emergency-blue" : "text-gray-400";
  const common = {
    className: "w-6 h-6",
    fill: "none",
    viewBox: "0 0 24 24",
    stroke: "currentColor",
  } as const;
  if (name === "home")
    return (
      <svg {...common}>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
        />
      </svg>
    );
  if (name === "report")
    return (
      <svg {...common}>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-7-7l7 7m0 0l-3 1 1-3"
        />
      </svg>
    );
  return (
    <svg {...common}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  );
}

const TABS = [
  { href: "/", label: "首页", icon: "home" },
  { href: "/report", label: "上报", icon: "report" },
  { href: "/profile", label: "我的", icon: "profile" },
];

export function BottomNav() {
  const pathname = usePathname();
  if (pathname === "/login") return null;
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 md:hidden">
      <div className="flex items-center justify-around h-16">
        {TABS.map((t) => {
          const active =
            t.href === "/" ? pathname === "/" : pathname.startsWith(t.href);
          return (
            <Link
              key={t.href}
              href={t.href}
              className="flex flex-col items-center justify-center w-full h-full"
            >
              <TabIcon name={t.icon} active={active} />
              <span
                className={`text-xs mt-0.5 ${
                  active ? "text-emergency-blue font-medium" : "text-gray-400"
                }`}
              >
                {t.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export function MobileHeader() {
  const pathname = usePathname();
  if (pathname === "/login") return null;
  return (
    <header className="md:hidden sticky top-0 z-40 bg-emergency-blue text-white shadow-sm">
      <div className="h-14 flex items-center justify-center px-4">
        <span className="text-base font-semibold tracking-wide">
          云南自然灾害应急·信息员端
        </span>
      </div>
    </header>
  );
}

export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  if (pathname === "/login") return null;
  const navLinks = [
    { h: "/", l: "首页" },
    { h: "/report", l: "上报" },
    { h: "/profile", l: "我的" },
  ];
  return (
    <header className="hidden md:block bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="w-7 h-7 rounded-lg bg-emergency-blue text-white flex items-center justify-center text-sm font-bold">
            滇
          </span>
          <span className="text-lg font-bold text-gray-800">
            云南自然灾害应急·信息员端
          </span>
        </Link>
        <nav className="flex items-center gap-8">
          {navLinks.map(({ h, l }) => {
            const active =
              h === "/" ? pathname === "/" : pathname.startsWith(h);
            return (
              <Link
                key={h}
                href={h}
                className={`text-sm font-medium ${
                  active
                    ? "text-emergency-blue"
                    : "text-gray-500 hover:text-emergency-blue"
                }`}
              >
                {l}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-4">
          {user ? (
            <>
              <span className="text-sm text-gray-500">{user.realName}</span>
              <button
                onClick={() => {
                  logout();
                  router.replace("/login");
                }}
                className="text-sm text-gray-400 hover:text-emergency-red"
              >
                退出
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="bg-emergency-blue text-white px-4 py-2 rounded-lg text-sm hover:bg-emergency-blue-dark"
            >
              登录
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
