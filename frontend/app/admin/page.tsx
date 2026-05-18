"use client";

import { useEffect, useMemo, useState } from "react";
import {
  adminCreateUser,
  adminGetLogTail,
  adminGetOverview,
  adminListUsers,
  adminResetDatabase,
  adminResetUserPassword,
  UserItem,
} from "@/lib/api";
import { getEmail, getToken, validateSession } from "@/lib/auth";

export default function AdminPage() {
  const [logFile, setLogFile] = useState("agent");
  const [logLines, setLogLines] = useState(120);

  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<"teacher" | "student">("teacher");
  const [resetEmail, setResetEmail] = useState("");
  const [resetPassword, setResetPassword] = useState("");

  const [overview, setOverview] = useState<any>(null);
  const [logData, setLogData] = useState<{ log_file: string; lines: string[] } | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);

  const [loadingOverview, setLoadingOverview] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [creatingUser, setCreatingUser] = useState(false);
  const [resettingPassword, setResettingPassword] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const logPreview = useMemo(() => (logData?.lines ?? []).join("\n"), [logData]);

  useEffect(() => {
    validateSession().then((me) => {
      if (!me || me.role !== "admin") {
        window.location.href = "/login";
      }
    });
  }, []);

  const authToken = getToken();

  async function handleLoadOverview() {
    setError(""); setStatus(""); setLoadingOverview(true);
    try {
      const res = await adminGetOverview(authToken);
      setOverview(res);
      setStatus("已刷新概览");
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取概览失败");
    } finally { setLoadingOverview(false); }
  }

  async function handleLoadLogs() {
    setError(""); setStatus(""); setLoadingLogs(true);
    try {
      const res = await adminGetLogTail(authToken, logFile.trim() || "agent", logLines);
      setLogData(res);
      setStatus(`已加载日志：${res.log_file}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取日志失败");
    } finally { setLoadingLogs(false); }
  }

  async function handleResetDatabase() {
    if (!window.confirm("确认重置数据库？\n将清空向量库、教材索引与去重记录，该操作不可撤销。")) return;
    setError(""); setStatus(""); setResetting(true);
    try {
      const res = await adminResetDatabase(authToken);
      setStatus(`数据库已重置，删除向量分片数：${res.deleted_vectors}`);
      setOverview(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置数据库失败");
    } finally { setResetting(false); }
  }

  async function handleLoadUsers() {
    setError(""); setStatus(""); setLoadingUsers(true);
    try {
      const list = await adminListUsers(authToken);
      setUsers(list);
      setStatus("已刷新用户列表");
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取用户列表失败");
    } finally { setLoadingUsers(false); }
  }

  async function handleCreateUser() {
    if (!newEmail.trim() || !newPassword.trim()) {
      setError("请填写邮箱和密码");
      return;
    }
    setError(""); setStatus(""); setCreatingUser(true);
    try {
      await adminCreateUser(authToken, { email: newEmail.trim(), password: newPassword, role: newRole });
      setStatus(`已创建${newRole === "teacher" ? "教师" : "学生"}账号：${newEmail}`);
      setNewEmail(""); setNewPassword("");
      await handleLoadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建账号失败");
    } finally { setCreatingUser(false); }
  }

  async function handleResetPassword() {
    if (!resetEmail.trim() || !resetPassword.trim()) {
      setError("请填写目标邮箱和新密码");
      return;
    }
    setError(""); setStatus(""); setResettingPassword(true);
    try {
      await adminResetUserPassword(authToken, resetEmail.trim(), resetPassword);
      setStatus(`已重置用户密码：${resetEmail}`);
      setResetEmail(""); setResetPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置密码失败");
    } finally { setResettingPassword(false); }
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1>管理员端</h1>
        <p>系统概览、账号管理、日志监控与数据库维护</p>
      </div>

      {/* System Overview */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h2>系统概览</h2>
            <p>当前登录：{getEmail() || "未登录"}</p>
          </div>
          <div className="btn-group">
            <button type="button" className="btn btn-secondary btn-sm" disabled={loadingOverview} onClick={handleLoadOverview}>
              {loadingOverview ? "加载中..." : "刷新概览"}
            </button>
            <button type="button" className="btn btn-danger btn-sm" disabled={resetting} onClick={handleResetDatabase}>
              {resetting ? "重置中..." : "重置数据库"}
            </button>
          </div>
        </div>

        {overview ? (
          <div className="metrics-grid" style={{ marginTop: 16, marginBottom: 0 }}>
            <div className="metric">
              <div className="metric-label">教材文件数</div>
              <div className="metric-value">{overview.knowledge_file_count}</div>
            </div>
            <div className="metric">
              <div className="metric-label">知识分片数</div>
              <div className="metric-value">{overview.knowledge_chunk_count}</div>
            </div>
            <div className="metric">
              <div className="metric-label">总问答数</div>
              <div className="metric-value">{overview.metrics_summary?.total_queries ?? 0}</div>
            </div>
            <div className="metric">
              <div className="metric-label">成功率</div>
              <div className="metric-value">{Number(overview.metrics_summary?.success_rate ?? 0).toFixed(1)}%</div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Users + Logs */}
      <div className="grid grid-2" style={{ alignItems: "start" }}>
        {/* User Management */}
        <div className="card">
          <div className="card-header">
            <h2>账号管理</h2>
            <p>创建教师/学生账号，重置密码</p>
          </div>

          <div className="section">
            <div className="section-title" style={{ fontSize: 14 }}>创建账号</div>
            <div className="form-group">
              <label className="form-label">邮箱</label>
              <input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} placeholder="teacher1@qq.com" />
            </div>
            <div className="form-group">
              <label className="form-label">初始密码</label>
              <input type="text" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="至少 6 位" />
            </div>
            <div className="form-group">
              <label className="form-label">角色</label>
              <select value={newRole} onChange={(e) => setNewRole(e.target.value as "teacher" | "student")}>
                <option value="teacher">教师</option>
                <option value="student">学生</option>
              </select>
            </div>
            <div className="btn-group">
              <button type="button" className="btn btn-primary btn-sm" disabled={creatingUser} onClick={handleCreateUser}>
                {creatingUser ? "创建中..." : "创建账号"}
              </button>
              <button type="button" className="btn btn-secondary btn-sm" disabled={loadingUsers} onClick={handleLoadUsers}>
                {loadingUsers ? "加载中..." : "刷新用户"}
              </button>
            </div>
          </div>

          <div className="divider" />

          <div className="section">
            <div className="section-title" style={{ fontSize: 14 }}>重置密码</div>
            <div className="form-group">
              <label className="form-label">目标邮箱</label>
              <input type="email" value={resetEmail} onChange={(e) => setResetEmail(e.target.value)} placeholder="student1@qq.com" />
            </div>
            <div className="form-group">
              <label className="form-label">新密码</label>
              <input type="text" value={resetPassword} onChange={(e) => setResetPassword(e.target.value)} placeholder="至少 6 位" />
            </div>
            <button type="button" className="btn btn-secondary btn-sm" disabled={resettingPassword} onClick={handleResetPassword}>
              {resettingPassword ? "重置中..." : "重置密码"}
            </button>
          </div>

          {users.length > 0 ? (
            <div style={{ marginTop: 12 }}>
              <div className="section-title" style={{ fontSize: 14 }}>用户列表</div>
              <div className="file-list">
                {users.map((u) => (
                  <div key={`${u.email}-${u.role}`} className="file-item">
                    <div className="file-item-info">
                      <div className="file-item-name">{u.email}</div>
                      <div className="file-item-meta">{u.role} / {u.is_active ? "启用" : "禁用"}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        {/* Logs */}
        <div className="card">
          <div className="card-header">
            <h2>日志监控</h2>
            <p>查看最近 N 行系统日志</p>
          </div>

          <div className="form-group">
            <label className="form-label">日志文件</label>
            <input value={logFile} onChange={(e) => setLogFile(e.target.value)} placeholder="agent" />
          </div>
          <div className="form-group">
            <label className="form-label">读取行数（1-1000）</label>
            <input
              type="number"
              min={1}
              max={1000}
              value={logLines}
              onChange={(e) => setLogLines(Math.max(1, Math.min(1000, Number(e.target.value || 1))))}
            />
          </div>
          <button type="button" className="btn btn-secondary btn-sm" disabled={loadingLogs} onClick={handleLoadLogs}>
            {loadingLogs ? "读取中..." : "读取日志"}
          </button>

          {logData ? (
            <div className="log-box">
              <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 0 }}>当前日志：{logData.log_file}</p>
              <pre>{logPreview || "（日志为空）"}</pre>
            </div>
          ) : null}
        </div>
      </div>

      {error ? <div className="alert alert-error">{error}</div> : null}
      {status ? <div className="alert alert-success">{status}</div> : null}
    </div>
  );
}
