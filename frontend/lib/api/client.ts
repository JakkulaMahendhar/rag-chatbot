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

/**
 * POSTs `body` and yields each Server-Sent Event payload as it arrives,
 * parsed from JSON. Separate from `request()` above because a streaming
 * body can't be awaited as one `response.json()` call - it has to be
 * read incrementally via `response.body`'s reader and split on SSE's
 * blank-line frame boundaries.
 *
 * Deliberately built on plain `fetch()`, not the browser's `EventSource`:
 * EventSource only supports GET with no custom headers, and this app
 * authenticates every request with an `Authorization: Bearer <token>`
 * header, which EventSource has no way to send.
 */
async function* stream<T>(path: string, body: unknown): AsyncGenerator<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  const token = tokenStorage.get();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Unable to reach the server. Check your connection.", 0);
  }

  if (!response.ok || !response.body) {
    throw await parseErrorResponse(response);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line; the last split piece
    // may be a not-yet-complete frame, so it's kept in the buffer
    // rather than parsed this round.
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith("data:")) continue;

      const payload = line.slice("data:".length).trim();
      if (payload) yield JSON.parse(payload) as T;
    }
  }
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) => request<T>("GET", path, options),
  post: <T>(path: string, options?: RequestOptions) => request<T>("POST", path, options),
  delete: <T>(path: string, options?: RequestOptions) => request<T>("DELETE", path, options),
  stream,
};
