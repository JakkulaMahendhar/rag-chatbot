import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """
    Fixed-window rate limiter keyed by client IP.

    Only effective within a single process - each worker has its
    own counters, so this does not enforce a global limit behind
    multiple Uvicorn/Gunicorn workers.
    """

    def __init__(self, max_attempts: int, window_seconds: int):

        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str):

        now = time.time()

        with self._lock:

            attempts = [
                t for t in self._hits[key] if now - t < self.window_seconds
            ]

            if len(attempts) >= self.max_attempts:

                retry_after = max(
                    1, int(self.window_seconds - (now - attempts[0]))
                )

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many attempts. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

            attempts.append(now)

            self._hits[key] = attempts


def rate_limit_dependency(limiter: InMemoryRateLimiter):

    def dependency(request: Request):

        client_ip = request.client.host if request.client else "unknown"

        limiter.check(client_ip)

    return dependency
