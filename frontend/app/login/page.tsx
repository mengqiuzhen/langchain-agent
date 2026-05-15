"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { authLogin } from "@/lib/api";
import { saveAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await authLogin(email.trim(), password);
      saveAuth({ token: res.access_token, role: res.role, email: res.email });
      router.push(res.role === "admin" ? "/admin" : res.role === "teacher" ? "/teacher" : "/student");
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 560, margin: "0 auto" }}>
      <h1>登录</h1>
      <p>账号由管理员创建后发放。当前系统已关闭公开注册。</p>

      <form onSubmit={handleSubmit}>
        <label>
          邮箱
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="example@qq.com" required />
        </label>

        <label>
          密码
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "登录中..." : "登录"}
        </button>
      </form>

      {error ? <p className="status">错误：{error}</p> : null}
    </div>
  );
}
