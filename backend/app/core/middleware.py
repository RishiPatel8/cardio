import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import redis.asyncio as aioredis

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Incoming Request: {request.method} {request.url.path} from client {client_ip}")
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        logger.info(f"Response Sent: status={response.status_code} in {process_time:.2f}ms")
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window_seconds

    async def dispatch(self, request: Request, call_next) -> Response:
        from app.core.dependencies import redis_client
        client_ip = request.client.host if request.client else "unknown_ip"
        key = f"rate_limit:{client_ip}:{request.url.path}"
        
        try:
            current_requests = await redis_client.get(key)
            if current_requests and int(current_requests) >= self.limit:
                logger.warning(f"Rate limit exceeded for client IP: {client_ip} on path {request.url.path}")
                return Response(
                    content="Too many requests. Please try again later.",
                    status_code=429,
                    media_type="text/plain"
                )
            
            # Increment request counter in Redis cache
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, self.window)
                await pipe.execute()
        except Exception as e:
            # Fallback gracefully if Redis connection is unavailable
            logger.warning(f"Rate Limiter Redis connection unavailable: {e}")
            
        return await call_next(request)
