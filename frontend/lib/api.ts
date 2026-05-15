export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type MetricsSummary = {
  total_queries: number;
  success_queries: number;
  success_rate: number;
  avg_latency_ms: number;
  tool_counts: Record<string, number>;
};

export type KnowledgeFileItem = {
  source: string;
  chunk_count: number;
  file_md5: string;
};

export type AdminOverview = {
  metrics_summary: MetricsSummary;
  knowledge_file_count: number;
  knowledge_chunk_count: number;
};

export type AdminResetResult = {
  ok: boolean;
  deleted_vectors: number;
};

export type AdminLogTail = {
  log_file: string;
  lines: string[];
};

export async function getSubjects(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/subjects`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("获取课程列表失败");
  }
  const data = (await response.json()) as { subjects: string[] };
  return data.subjects;
}

export async function getMetricsSummary(token: string): Promise<MetricsSummary> {
  const response = await fetch(`${API_BASE_URL}/api/metrics/summary`, {
    headers: withAuthHeaders(token),
    cache: "no-store",
  });
  const data = (await response.json()) as MetricsSummary & { detail?: string };
  if (!response.ok) {
    throw new Error(data.detail ?? "获取运行指标失败");
  }
  return data;
}

export async function getKnowledgeFiles(): Promise<KnowledgeFileItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/files`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("获取教材列表失败");
  }
  const data = (await response.json()) as { files: KnowledgeFileItem[] };
  return data.files ?? [];
}

export async function deleteKnowledgeFile(fileMd5: string): Promise<{ deleted: boolean; deleted_chunks: number }> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/file?file_md5=${encodeURIComponent(fileMd5)}`, {
    method: "DELETE",
  });
  const data = (await response.json()) as { deleted?: boolean; deleted_chunks?: number; detail?: string };
  if (!response.ok) {
    throw new Error(data.detail ?? "删除教材失败");
  }
  return {
    deleted: Boolean(data.deleted),
    deleted_chunks: Number(data.deleted_chunks ?? 0),
  };
}

export type UserRole = "admin" | "teacher" | "student";

export type AuthResult = {
  access_token: string;
  token_type: string;
  role: UserRole;
  email: string;
};

export type MeResult = {
  email: string;
  role: UserRole;
};

export type UserItem = {
  email: string;
  role: "teacher" | "student" | "admin";
  is_active: boolean;
  created_at: number;
};

function withAuthHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
  };
}

export async function adminGetOverview(token: string): Promise<AdminOverview> {
  const response = await fetch(`${API_BASE_URL}/api/admin/overview`, {
    headers: withAuthHeaders(token),
    cache: "no-store",
  });

  const data = (await response.json()) as AdminOverview & { detail?: string };
  if (!response.ok) {
    throw new Error(data.detail ?? "获取管理员概览失败");
  }
  return data;
}

export async function adminResetDatabase(token: string): Promise<AdminResetResult> {
  const response = await fetch(`${API_BASE_URL}/api/admin/reset-db`, {
    method: "POST",
    headers: withAuthHeaders(token),
  });

  const data = (await response.json()) as AdminResetResult & { detail?: string };
  if (!response.ok) {
    throw new Error(data.detail ?? "重置数据库失败");
  }
  return data;
}

export async function adminGetLogTail(token: string, file: string, lines = 100): Promise<AdminLogTail> {
  const params = new URLSearchParams({
    file,
    lines: String(lines),
  });

  const response = await fetch(`${API_BASE_URL}/api/admin/logs/tail?${params.toString()}`, {
    headers: withAuthHeaders(token),
    cache: "no-store",
  });

  const data = (await response.json()) as AdminLogTail & { detail?: string };
  if (!response.ok) {
    throw new Error(data.detail ?? "获取日志失败");
  }
  return data;
}

export async function authSendCode(email: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/auth/send-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const data = (await response.json()) as { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? "发送验证码失败");
}

export async function authRegister(email: string, code: string, password: string): Promise<AuthResult> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code, password }),
  });
  const data = (await response.json()) as AuthResult & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? "注册失败");
  return data;
}

export async function authLogin(email: string, password: string): Promise<AuthResult> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = (await response.json()) as AuthResult & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? "登录失败");
  return data;
}

export async function authMe(token: string): Promise<MeResult> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: withAuthHeaders(token),
    cache: "no-store",
  });
  const data = (await response.json()) as MeResult & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? "获取用户信息失败");
  return data;
}

export async function adminCreateUser(
  token: string,
  payload: { email: string; password: string; role: "teacher" | "student" }
): Promise<UserItem> {
  const response = await fetch(`${API_BASE_URL}/api/auth/users`, {
    method: "POST",
    headers: {
      ...withAuthHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = (await response.json()) as UserItem & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? "创建账号失败");
  return data;
}

export async function adminListUsers(token: string): Promise<UserItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/auth/users`, {
    headers: withAuthHeaders(token),
    cache: "no-store",
  });
  const data = (await response.json()) as (UserItem[] & { detail?: string });
  if (!response.ok) {
    const err = data as unknown as { detail?: string };
    throw new Error(err.detail ?? "获取用户列表失败");
  }
  return data as UserItem[];
}

export async function adminResetUserPassword(token: string, email: string, newPassword: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/auth/users/reset-password`, {
    method: "POST",
    headers: {
      ...withAuthHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, new_password: newPassword }),
  });
  const data = (await response.json()) as { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? "重置用户密码失败");
}
