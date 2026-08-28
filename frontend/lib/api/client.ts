import { ApiError, parseErrorResponse } from "@/lib/errors/api-error";
import { tokenStorage } from "@/lib/auth/token";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  // Fails loudly at build/dev time rather than silently hitting a
  // relative URL that happens to 404 - see .env.example.
  throw new Error("NEXT_PUBLIC_API_URL is not set");
}

interface RequestOptions {
  auth?: boolean;
  body?: unknown;
  formData?: FormData;
}

async function request<T>(
  method: string,
  path: string,
  { auth = true, body, formData }: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {};

  if (auth) {
    const token = tokenStorage.get();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let requestBody: BodyInit | undefined;

  if (formData) {
    requestBody = formData;
    // Deliberately no Content-Type - the browser sets the multipart
    // boundary itself when given a FormData body.
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    requestBody = JSON.stringify(body);
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: requestBody,
    });
  } catch {
    throw new ApiError("Unable to reach the server. Check your connection.", 0);
  }

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  if (response.status === 204 || response.headers.get("Content-Length") === "0") {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) => request<T>("GET", path, options),
  post: <T>(path: string, options?: RequestOptions) => request<T>("POST", path, options),
  delete: <T>(path: string, options?: RequestOptions) => request<T>("DELETE", path, options),
};
