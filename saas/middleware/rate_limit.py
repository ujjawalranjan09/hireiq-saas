# Rate Limit Middleware - Limits requests per IP address using Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis.asyncio as redis
import os
import time

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT_REQUESTS = 100  # Maximum requests per window
RATE_LIMIT_WINDOW = 60  # Window size in seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that uses Redis to count how many requests a given IP address
    has made in the last 60 seconds.
    
    If the count exceeds 100 requests per minute, it returns a 429 Too Many Requests response.
    """
    
    def __init__(self, app, redis_client: redis.Redis = None):
        super().__init__(app)
        self.redis_client = redis_client
    
    async def get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        return self.redis_client
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Try to connect to Redis and check rate limit
        try:
            r = await self.get_redis_client()
            
            # Create a key for this IP
            key = f"rate_limit:{client_ip}"
            
            # Get current count
            current_count = await r.get(key)
            
            if current_count is None:
                # First request in this window
                await r.setex(key, RATE_LIMIT_WINDOW, 1)
            else:
                current_count = int(current_count)
                
                if current_count >= RATE_LIMIT_REQUESTS:
                    # Rate limit exceeded
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": "Too many requests",
                            "message": f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
                        }
                    )
                
                # Increment counter
                await r.incr(key)
            
        except redis.exceptions.RedisError:
            # If Redis is unavailable, skip rate limiting but log the error
            # In production, you might want to fail open or closed based on your requirements
            pass
        except Exception:
            # Any other error, skip rate limiting
            pass
        
        # Continue with the request
        response = await call_next(request)
        return response
