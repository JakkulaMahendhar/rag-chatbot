import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import logger
from app.core.request_context import set_request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        request_id = uuid4().hex[:8]

        set_request_id(request_id)

        start = time.time()

        logger.info(
            f"{request.method} {request.url.path} started"
        )

        response = await call_next(request)

        duration = round(
            time.time() - start,
            3
        )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            f"{request.method} {request.url.path} "
            f"{response.status_code} "
            f"{duration}s"
        )

        return response