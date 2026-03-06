import type { ITokenResponse } from "./types";

const ACCESS_TOKEN_KEY = "cm_access_token";
const REFRESH_TOKEN_KEY = "cm_refresh_token";
const USER_KEY = "cm_user";

export interface StoredUser {
  id: string;
  username: string | null;
  full_name: string | null;
  role: string | null;
}

export function saveTokens(tokens: ITokenResponse): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  localStorage.setItem(
    USER_KEY,
    JSON.stringify({
      id: tokens.user_id,
      username: tokens.username,
      full_name: tokens.full_name,
      role: tokens.role,
    })
  );
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getCurrentUser(): StoredUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function clearAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

/** Returns true if the current user has one of the given roles */
export function hasRole(...roles: string[]): boolean {
  const user = getCurrentUser();
  return !!user?.role && roles.includes(user.role);
}

export const STAFF_ROLES = ["psychologist", "rehab_staff", "hospital_admin", "researcher", "doctor", "admin"];
export const ADMIN_ROLES = ["admin"];
