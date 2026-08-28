// Mirrors app/auth/schemas.py

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface UserResponse {
  id: number;
  email: string;
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// GET /auth/me returns only id/email (app/auth/router.py) - not the full
// UserResponse shape returned by /auth/register.
export interface CurrentUser {
  id: number;
  email: string;
}
