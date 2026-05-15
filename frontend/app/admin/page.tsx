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
  const [token, setToken] = useState("");
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

  const authToken = token.trim() || getToken();

  useEffect(() => {
    validateSession().then((me) => {
      if (!me || me.role !== "admin") {
        window.location.href = "/login";
      }
    });
  }, []);

  async function handleLoadOverview() {
    if (!authToken) {
      setError("请先登录管理员账号，或手动输入 Bearer Token");
      return;
    }

    setError("");
    setStatus("");
    setLoadingOverview(true);
    try {
      const res = await adminGetOverview(authToken);
      setOverview(res);
      setStatus("已刷新管理员概览");
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取管理员概览失败");
    } finally {
      setLoadingOverview(false);
    }
  }

  async function handleLoadLogs() {
    if (!authToken) {
      setError("请先登录管理员账号，或手动输入 Bearer Token");
      return;
    }

    setError("");
    setStatus("");
    setLoadingLogs(true);
    try {
      const res = await adminGetLogTail(authToken, logFile.trim() || "agent", logLines);
      setLogData(res);
      setStatus(`已加载日志：${res.log_file}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取日志失败");
    } finally {
      setLoadingLogs(false);
    }
  }

  async function handleResetDatabase() {
    if (!authToken) {
      setError("请先登录管理员账号，或手动输入 Bearer Token");
      return;
    }

    const ok = window.confirm("确认重置数据库？\n将清空向量库、教材索引与去重记录，该操作不可撤销。");
    if (!ok) {
      return;
    }

    setError("");
    setStatus("");
    setResetting(true);
    try {
      const res = await adminResetDatabase(authToken);
      setStatus(`数据库已重置，删除向量分片数：${res.deleted_vectors}`);
      setOverview(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置数据库失败");
    } finally {
      setResetting(false);
    }
  }

  async function handleLoadUsers() {
    if (!authToken) {
      setError("请先登录管理员账号，或手动输入 Bearer Token");
      return;
    }
    setError("");
    setStatus("");
    setLoadingUsers(true);
    try {
      const list = await adminListUsers(authToken);
      setUsers(list);
      setStatus("已刷新用户列表");
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取用户列表失败");
    } finally {
      setLoadingUsers(false);
    }
  }

  async function handleCreateUser() {
    if (!authToken) {
      setError("请先登录管理员账号，或手动输入 Bearer Token");
      return;
    }
    if (!newEmail.trim() || !newPassword.trim()) {
      setError("请填写邮箱和密码");
      return;
    }

    setError("");
    setStatus("");
    setCreatingUser(true);
    try {
      await adminCreateUser(authToken, {
        email: newEmail.trim(),
        password: newPassword,
        role: newRole,
      });
      setStatus(`已创建${newRole === "teacher" ? "教师" : "学生"}账号：${newEmail}`);
      setNewEmail("");
      setNewPassword("");
      await handleLoadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建账号失败");
    } finally {
      setCreatingUser(false);
    }
  }

  async function handleResetPassword() {
    if (!authToken) {
      setError("请先登录管理员账号，或手动输入 Bearer Token");
      return;
    }
    if (!resetEmail.trim() || !resetPassword.trim()) {
      setError("请填写目标邮箱和新密码");
      return;
    }

    setError("");
    setStatus("");
    setResettingPassword(true);
    try {
      await adminResetUserPassword(authToken, resetEmail.trim(), resetPassword);
      setStatus(`已重置用户密码：${resetEmail}`);
      setResetEmail("");
      setResetPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置用户密码失败");
    } finally {
      setResettingPassword(false);
    }
  }

  return (
    <div className="grid" style={{ alignItems: "start" }}>
      <div className="card">
        <h1>管理员端</h1>
        <p>当前登录邮箱：{getEmail() || "未登录"}</p>
        <p>支持：数据库重置、日志监控、教师/学生账号分配。</p>

        <label>
          管理员 Bearer Token（可选，不填则使用当前登录态）
          <input type="password" value={token} onChange={(e) => setToken(e.target.value)} placeholder="可留空" />
        </label>

        <div className="admin-action-grid">
          <button type="button" disabled={loadingOverview} onClick={handleLoadOverview}>
            {loadingOverview ? "刷新中..." : "刷新概览"}
          </button>
          <button type="button" disabled={resetting} onClick={handleResetDatabase}>
            {resetting ? "重置中..." : "重置数据库"}
          </button>
        </div>

        {error ? <p className="status">错误：{error}</p> : null}
        {status ? <p className="status">状态：{status}</p> : null}

        {overview ? (
          <div className="card" style={{ marginTop: 16 }}>
            <h3>系统概览</h3>
            <p>教材文件数：{overview.knowledge_file_count}</p>
            <p>知识分片数：{overview.knowledge_chunk_count}</p>
            <p>总问答数：{overview.metrics_summary?.total_queries ?? 0}</p>
            <p>问答成功率：{Number(overview.metrics_summary?.success_rate ?? 0).toFixed(1)}%</p>
            <p>平均耗时：{Number(overview.metrics_summary?.avg_latency_ms ?? 0).toFixed(0)} ms</p>
          </div>
        ) : null}
      </div>

      <div className="card">
        <h2>账号分配（管理员）</h2>
        <p>建议由管理员创建教师/学生账号，统一发放初始密码。</p>

        <label>
          邮箱
          <input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} placeholder="teacher1@qq.com" />
        </label>

        <label>
          初始密码
          <input type="text" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="至少6位" />
        </label>

        <label>
          角色
          <select value={newRole} onChange={(e) => setNewRole(e.target.value as "teacher" | "student")}>
            <option value="teacher">教师</option>
            <option value="student">学生</option>
          </select>
        </label>

        <div className="admin-action-grid">
          <button type="button" disabled={creatingUser} onClick={handleCreateUser}>
            {creatingUser ? "创建中..." : "创建账号"}
          </button>
          <button type="button" disabled={loadingUsers} onClick={handleLoadUsers}>
            {loadingUsers ? "加载中..." : "刷新用户列表"}
          </button>
        </div>

        <div className="card" style={{ marginTop: 12 }}>
          <h3>重置用户密码</h3>
          <label>
            目标邮箱
            <input type="email" value={resetEmail} onChange={(e) => setResetEmail(e.target.value)} placeholder="student1@qq.com" />
          </label>
          <label>
            新密码
            <input type="text" value={resetPassword} onChange={(e) => setResetPassword(e.target.value)} placeholder="至少6位" />
          </label>
          <button type="button" disabled={resettingPassword} onClick={handleResetPassword}>
            {resettingPassword ? "重置中..." : "重置该用户密码"}
          </button>
        </div>

        <div className="log-box" style={{ marginTop: 12 }}>
          {users.length === 0 ? (
            <p>暂无用户数据</p>
          ) : (
            <ul className="tool-list">
              {users.map((u) => (
                <li key={`${u.email}-${u.role}`}>
                  {u.email} / {u.role} / {u.is_active ? "启用" : "禁用"}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="card">
        <h2>日志监控</h2>

        <label>
          日志文件名（默认 agent，会自动补 .log）
          <input value={logFile} onChange={(e) => setLogFile(e.target.value)} placeholder="如：agent 或 agent_20260421" />
        </label>

        <label>
          读取行数（1 - 1000）
          <input
            type="number"
            min={1}
            max={1000}
            value={logLines}
            onChange={(e) => setLogLines(Math.max(1, Math.min(1000, Number(e.target.value || 1))))}
          />
        </label>

        <button type="button" disabled={loadingLogs} onClick={handleLoadLogs}>
          {loadingLogs ? "读取中..." : "读取日志"}
        </button>

        <div className="log-box" style={{ marginTop: 12 }}>
          {logData ? (
            <>
              <p style={{ marginTop: 0 }}>当前日志：{logData.log_file}</p>
              <pre>{logPreview || "（日志为空）"}</pre>
            </>
          ) : (
            <p>尚未读取日志</p>
          )}
        </div>
      </div>
    </div>
  );
}
