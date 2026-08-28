const TOKEN_KEY = "rag_chatbot_token";

/**
 * The backend issues short-lived JWTs (30 min, no refresh token - see
 * app/auth/jwt.py) and has no server-side session concept, so there's
 * nothing for Next.js to do on the server for auth. Token lives in
 * localStorage; expiry is handled by reacting to 401s, not by tracking
 * the expiry client-side.
 */
export const tokenStorage = {
  get(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(TOKEN_KEY);
  },
  set(token: string) {
    window.localStorage.setItem(TOKEN_KEY, token);
  },
  clear() {
    window.localStorage.removeItem(TOKEN_KEY);
  },
};
