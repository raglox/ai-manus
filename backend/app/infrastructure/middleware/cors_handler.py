"""
CORS Handler Middleware
Ensures CORS headers are present on all responses including error responses
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class CORSHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure CORS headers are always present.
    This is especially important for error responses which might skip the main CORS middleware.
    """
    
    def __init__(self, app, allowed_origins: list[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        logger.info(f"CORSHeaderMiddleware initialized with origins: {self.allowed_origins}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get the origin from request
        origin = request.headers.get("origin", "")
        
        # Determine if origin is allowed
        allowed_origin = "*"
        if origin and "*" not in self.allowed_origins:
            if origin in self.allowed_origins:
                allowed_origin = origin
            else:
                allowed_origin = self.allowed_origins[0] if self.allowed_origins else "*"
        elif origin:
            allowed_origin = origin
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "3600"
            response.headers["Access-Control-Expose-Headers"] = "*"
            return response
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise
        
        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
        
        return response
