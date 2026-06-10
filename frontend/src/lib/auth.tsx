import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { login as apiLogin, selectCompany as apiSelectCompany } from "@/api/auth";
import { clearTokens, getAccessToken, setTokens } from "@/api/client";
import type { CompanyBrief, TokenResponse } from "@/api/types";

interface Profile {
  companyId: string | null;
  role: string | null;
  companyName: string | null;
  companies: CompanyBrief[];
}

interface AuthContextValue {
  isAuthed: boolean;
  hasTenant: boolean;
  profile: Profile | null;
  login: (email: string, password: string) => Promise<TokenResponse>;
  selectCompany: (companyId: string) => Promise<void>;
  logout: () => void;
}

const PROFILE_KEY = "solidita.profile";
const Ctx = createContext<AuthContextValue | null>(null);

function loadProfile(): Profile | null {
  const raw = localStorage.getItem(PROFILE_KEY);
  return raw ? (JSON.parse(raw) as Profile) : null;
}

function applyToken(res: TokenResponse): Profile {
  setTokens(res.access_token, res.refresh_token);
  const companyName = res.company_id
    ? (res.companies.find((c) => c.id === res.company_id)?.name ?? null)
    : null;
  const profile: Profile = {
    companyId: res.company_id,
    role: res.role,
    companyName,
    companies: res.companies,
  };
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  return profile;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(loadProfile());
  const [token, setToken] = useState<string | null>(getAccessToken());

  async function login(email: string, password: string): Promise<TokenResponse> {
    const res = await apiLogin(email, password);
    setProfile(applyToken(res));
    setToken(res.access_token);
    return res;
  }

  async function selectCompany(companyId: string): Promise<void> {
    const res = await apiSelectCompany(companyId);
    setProfile(applyToken(res));
    setToken(res.access_token);
  }

  function logout(): void {
    clearTokens();
    localStorage.removeItem(PROFILE_KEY);
    setProfile(null);
    setToken(null);
  }

  // when a silent refresh fails, api/client emits this — drop to the login screen
  useEffect(() => {
    const onUnauthorized = () => logout();
    window.addEventListener("solidita:unauthorized", onUnauthorized);
    return () => window.removeEventListener("solidita:unauthorized", onUnauthorized);
  }, []);

  const value: AuthContextValue = {
    isAuthed: Boolean(token),
    hasTenant: Boolean(token) && Boolean(profile?.companyId),
    profile,
    login,
    selectCompany,
    logout,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
