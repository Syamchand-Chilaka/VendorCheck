"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { getSession, signIn, signOut, signUp, confirmSignUp } from "@/lib/auth";
import type { MeResponse } from "@/lib/types";
import { getMe } from "@/lib/api";

interface AuthState {
  loading: boolean;
  authenticated: boolean;
  user: MeResponse | null;
  tenantId: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    displayName: string,
  ) => Promise<void>;
  confirm: (email: string, code: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<MeResponse | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);

  const loadUser = useCallback(async () => {
    try {
      const session = await getSession();
      if (!session) {
        setAuthenticated(false);
        setUser(null);
        setTenantId(null);
        return;
      }
      // Call /me to get workspace info — workspace is auto-created on first call
      const me = await getMe("");
      setUser(me);
      setTenantId(me.workspace.id);
      setAuthenticated(true);
    } catch {
      setAuthenticated(false);
      setUser(null);
      setTenantId(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      await signIn(email, password);
      await loadUser();
    },
    [loadUser],
  );

  const register = useCallback(
    async (email: string, password: string, displayName: string) => {
      await signUp(email, password, displayName);
    },
    [],
  );

  const confirm = useCallback(
    async (email: string, code: string) => {
      await confirmSignUp(email, code);
    },
    [],
  );

  const logout = useCallback(() => {
    signOut();
    setAuthenticated(false);
    setUser(null);
    setTenantId(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        loading,
        authenticated,
        user,
        tenantId,
        login,
        register,
        confirm,
        logout,
        refresh: loadUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
