"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { clearAuth, getEmail, getRole, validateSession } from "@/lib/auth";

type Role = "" | "admin" | "teacher" | "student";

export default function NavClient() {
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
    if (!role) return [{ href: "/", label: "概览" }];

    if (role === "admin") {
      return [
        { href: "/", label: "概览" },
        { href: "/admin", label: "管理员端" },
        { href: "/teacher", label: "教师端" },
        { href: "/student", label: "学生端" },
        { href: "/metrics", label: "运行指标" },
      ];
    }

    if (role === "teacher") {
      return [
        { href: "/", label: "概览" },
        { href: "/teacher", label: "教师端" },
        { href: "/student", label: "学生端" },
      ];
    }

    return [
      { href: "/", label: "概览" },
      { href: "/student", label: "学生端" },
    ];
  }, [role]);

  return (
    <div className="nav">
      {links.map((item) => (
        <Link key={item.href} href={item.href}>
          {item.label}
        </Link>
      ))}

      {role ? <span className="nav-user">当前登录：{email}（{role}）</span> : null}

      {role ? (
        <button
          type="button"
          onClick={() => {
            clearAuth();
            setRole("");
            setEmail("");
            window.location.href = "/login";
          }}
          style={{ maxWidth: 140 }}
        >
          退出登录
        </button>
      ) : (
        <Link href="/login">登录</Link>
      )}
    </div>
  );
}
