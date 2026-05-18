import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import NavClient from "@/app/components/nav-client";

export const metadata: Metadata = {
  title: "AI 教学助手",
  description: "FastAPI + Next.js 版 AI 教学助手",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="layout">
          <NavClient />
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
