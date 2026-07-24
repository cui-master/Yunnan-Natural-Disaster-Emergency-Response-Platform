"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { LoginResult } from "@/lib/types";
import { getMe, login as apiLogin } from "@/lib/api";
import {
  clearUser,
  getToken,
  getUser,
  removeToken,
  setToken,
  setUser,
} from "@/lib/storage";

interface AuthContextValue {
  user: LoginResult | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<LoginResult | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // 初次挂载：读取本地 token，并尝试用 /api/auth/me 刷新用户信息
  useEffect(() => {
    const storedToken = getToken();
    const storedUser = getUser();
    if (storedToken && storedUser) {
      setTokenState(storedToken);
      setUserState(storedUser);
      // 后台用 me 接口校验/刷新
      getMe()
        .then((fresh) => {
          setUserState(fresh);
          setUser(fresh);
        })
        .catch(() => {
          // token 失效则清空
          doLogout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const doLogin = useCallback(async (username: string, password: string) => {
    const data = await apiLogin(username, password);
    setToken(data.token);
    setUser(data);
    setTokenState(data.token);
    setUserState(data);
  }, []);

  const doLogout = useCallback(() => {
    removeToken();
    clearUser();
    setTokenState(null);
    setUserState(null);
  }, []);

  const value: AuthContextValue = {
    user,
    token,
    loading,
    login: doLogin,
    logout: doLogout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth 必须在 AuthProvider 内使用");
  }
  return ctx;
}
