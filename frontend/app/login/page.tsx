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
    <div className="login-page">
      <div className="login-card animate-in">
        <div className="card">
          <div className="login-logo">
            <div className="login-logo-icon" />
            <span className="login-logo-text">AI 教学助手</span>
          </div>

          <p style={{ textAlign: "center", color: "var(--text-secondary)", fontSize: 14, marginBottom: 28 }}>
            账号由管理员创建后发放
          </p>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">邮箱</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="example@qq.com"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">密码</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={6}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
              {loading ? "登录中..." : "登录"}
            </button>
          </form>

          {error ? <div className="alert alert-error">{error}</div> : null}
        </div>
      </div>
    </div>
  );
}
