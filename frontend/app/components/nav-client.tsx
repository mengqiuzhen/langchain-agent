"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { clearAuth, getEmail, getRole, validateSession } from "@/lib/auth";

type Role = "" | "admin" | "teacher" | "student";

const ROLE_LABELS: Record<string, string> = {
  admin: "管理员",
  teacher: "教师",
  student: "学生",
};

export default function NavClient() {
  const pathname = usePathname();
  const [role, setRole] = useState<Role>("");
  const [email, setEmail] = useState("");

  useEffect(() => {
    const syncAuthState = () => {
      const localRole = getRole() as Role;
      const localEmail = getEmail();
      setRole(localRole || "");
      setEmail(localEmail || "");

      validateSession().then((me) => {
        if (me?.role) {
          setRole(me.role as Role);
          setEmail(me.email);
        } else {
          setRole("");
          setEmail("");
        }
      });
    };

    syncAuthState();
    window.addEventListener("auth-changed", syncAuthState);
    window.addEventListener("storage", syncAuthState);

    return () => {
      window.removeEventListener("auth-changed", syncAuthState);
      window.removeEventListener("storage", syncAuthState);
    };
  }, []);

  const links = useMemo(() => {
    if (!role) return [{ href: "/", label: "概览", icon: "🏠" }];

    if (role === "admin") {
      return [
        { href: "/", label: "概览", icon: "🏠" },
        { href: "/admin", label: "管理员端", icon: "⚙️" },
        { href: "/teacher", label: "教师端", icon: "📚" },
        { href: "/student", label: "学生端", icon: "🎓" },
        { href: "/metrics", label: "运行指标", icon: "📊" },
      ];
    }

    if (role === "teacher") {
      return [
        { href: "/", label: "概览", icon: "🏠" },
        { href: "/teacher", label: "教师端", icon: "📚" },
        { href: "/student", label: "学生端", icon: "🎓" },
      ];
    }

    return [
      { href: "/", label: "概览", icon: "🏠" },
      { href: "/student", label: "学生端", icon: "🎓" },
    ];
  }, [role]);

  const avatarLetter = email ? email.charAt(0).toUpperCase() : "?";

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon" />
        <span className="sidebar-logo-text">AI 教学助手</span>
      </div>

      <nav className="sidebar-nav">
        {links.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={pathname === item.href ? "active" : ""}
          >
            <span className="sidebar-nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        {role ? (
          <>
            <div className="sidebar-user">
              <div className="sidebar-user-avatar">{avatarLetter}</div>
              <div className="sidebar-user-info">
                <span className="sidebar-user-email">{email}</span>
                <span className="sidebar-user-role">{ROLE_LABELS[role] || role}</span>
              </div>
            </div>
            <button
              type="button"
              className="sidebar-logout"
              onClick={() => {
                clearAuth();
                setRole("");
                setEmail("");
                window.location.href = "/login";
              }}
            >
              退出登录
            </button>
          </>
        ) : (
          <Link href="/login" className="btn btn-primary btn-block btn-sm">
            登录
          </Link>
        )}
      </div>
    </aside>
  );
}
