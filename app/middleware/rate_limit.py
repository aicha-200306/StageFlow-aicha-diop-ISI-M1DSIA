import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request, call_next):
        identifier = request.headers.get("authorization") or (request.client.host if request.client else "anonymous")
        now = time.time()
        self.hits[identifier] = [t for t in self.hits[identifier] if now - t < self.window_seconds]
        if len(self.hits[identifier]) >= self.max_requests:
            return JSONResponse(status_code=429, content={"detail": "Trop de requêtes, réessayez plus tard."})
        self.hits[identifier].append(now)
        return await call_next(request)