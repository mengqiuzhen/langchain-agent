"use client";

import { authMe, type MeResult, type UserRole } from "@/lib/api";

const TOKEN_KEY = "ai_teach_token";
const ROLE_KEY = "ai_teach_role";
const EMAIL_KEY = "ai_teach_email";

export function saveAuth(auth: { token: string; role: UserRole; email: string }) {
  localStorage.setItem(TOKEN_KEY, auth.token);
  localStorage.setItem(ROLE_KEY, auth.role);
  localStorage.setItem(EMAIL_KEY, auth.email);
  window.dispatchEvent(new Event("auth-changed"));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(EMAIL_KEY);
  window.dispatchEvent(new Event("auth-changed"));
}

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function getRole(): UserRole | "" {
  return (localStorage.getItem(ROLE_KEY) as UserRole | null) ?? "";
}

export function getEmail(): string {
  return localStorage.getItem(EMAIL_KEY) ?? "";
}

export async function validateSession(): Promise<MeResult | null> {
  const token = getToken();
  if (!token) return null;

  try {
    return await authMe(token);
  } catch {
    clearAuth();
    return null;
  }
}
