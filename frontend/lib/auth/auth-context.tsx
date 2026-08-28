"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";
import { tokenStorage } from "@/lib/auth/token";
import { ApiError } from "@/lib/errors/api-error";
import type { CurrentUser } from "@/types/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: CurrentUser | null;
  status: AuthStatus;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  // Session restoration: the backend has no server-side session, just a
  // 30-minute JWT with no refresh token (app/auth/jwt.py) - on load,
  // validate whatever token is in storage by actually calling /auth/me
  // rather than trusting it blindly.
  useEffect(() => {
    const token = tokenStorage.get();

    // Routes both "no token" and "invalid token" through .catch() so
    // every setState call happens inside a promise callback, not
    // synchronously in the effect body.
    (token ? authApi.me() : Promise.reject())
      .then((currentUser) => {
        setUser(currentUser);
        setStatus("authenticated");
      })
      .catch(() => {
        tokenStorage.clear();
        setStatus("unauthenticated");
      });
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await authApi.login({ email, password });
    tokenStorage.set(access_token);

    const currentUser = await authApi.me();
    setUser(currentUser);
    setStatus("authenticated");
  }, []);

  const register = useCallback(
    async (email: string, password: string) => {
      await authApi.register({ email, password });
      // /auth/register returns the created user, not a token (see
      // app/auth/router.py) - log in immediately after for a seamless
      // flow, using the same real /auth/login call the login form uses.
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  return (
    <AuthContext.Provider value={{ user, status, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
