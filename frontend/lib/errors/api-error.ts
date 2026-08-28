/**
 * Normalized shape for every API failure, regardless of whether it came
 * from FastAPI's HTTPException (`{"detail": "..."}`), a 422 validation
 * error (`{"detail": [{"msg": "...", ...}, ...]}`), or the network itself
 * (no response at all). Components only ever need `.message` and
 * `.status` - never raw backend payloads or stack traces.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly retryAfterSeconds?: number;

  constructor(message: string, status: number, retryAfterSeconds?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
  }

  get isUnauthorized() {
    return this.status === 401;
  }

  get isForbidden() {
    return this.status === 403;
  }

  get isRateLimited() {
    return this.status === 429;
  }

  get isNetworkError() {
    return this.status === 0;
  }
}

interface FastApiValidationErrorItem {
  msg?: string;
  loc?: (string | number)[];
}

export async function parseErrorResponse(response: Response): Promise<ApiError> {
  const retryAfterHeader = response.headers.get("Retry-After");
  const retryAfterSeconds = retryAfterHeader ? Number(retryAfterHeader) : undefined;

  let message = `Request failed (${response.status})`;

  try {
    const body = await response.json();

    if (typeof body?.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body?.detail)) {
      const items = body.detail as FastApiValidationErrorItem[];
      message = items.map((item) => item.msg).filter(Boolean).join(", ") || message;
    }
  } catch {
    // Response wasn't JSON (or was empty) - keep the generic message.
  }

  return new ApiError(message, response.status, retryAfterSeconds);
}
