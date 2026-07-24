import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/AuthProvider";
import { ToastProvider } from "@/components/ToastProvider";
import { TopNav, BottomNav, MobileHeader } from "@/components/Navigation";

export const metadata: Metadata = {
  title: "云南自然灾害应急·信息员端",
  description: "云南省自然灾害应急响应平台 - 普通信息员（ROLE_REPORTER）移动端",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#1d4ed8",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <AuthProvider>
          <ToastProvider>
            <TopNav />
            <MobileHeader />
            <main className="min-h-screen bg-[#f3f4f6] pb-16 md:pb-0">
              {children}
            </main>
            <BottomNav />
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
