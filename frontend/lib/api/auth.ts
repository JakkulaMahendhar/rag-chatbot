import { apiClient } from "@/lib/api/client";
import type {
  CurrentUser,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserResponse,
} from "@/types/auth";

export const authApi = {
  register: (payload: RegisterRequest) =>
    apiClient.post<UserResponse>("/auth/register", { body: payload, auth: false }),

  login: (payload: LoginRequest) =>
    apiClient.post<TokenResponse>("/auth/login", { body: payload, auth: false }),

  me: () => apiClient.get<CurrentUser>("/auth/me"),
};
