from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from collections import defaultdict
import time


request_counter = defaultdict(list)
MAX_REQUESTS = 2
TIME_WINDOW = 60  # Sec


class DdosProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        ip = request.client.host
        now = time.time()

        # Delete old requests
        request_counter[ip] = [t for t in request_counter[ip] if now - t < TIME_WINDOW]

        # Add new request
        request_counter[ip].append(now)

        # Check count of requests
        if len(request_counter[ip]) >= MAX_REQUESTS:
            return Response(
                content="Too many requests from your IP address",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )

        return await call_next(request)
