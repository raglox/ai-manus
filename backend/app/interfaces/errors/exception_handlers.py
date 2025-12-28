from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
import logging
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.application.errors.exceptions import AppException
from app.interfaces.schemas.base import APIResponse

logger = logging.getLogger(__name__)


def _add_cors_headers(response: JSONResponse, request: Request) -> JSONResponse:
    """Add CORS headers to response"""
    origin = request.headers.get("origin", "*")
    
    # Allow specific origins or all
    allowed_origins = [
        "http://34.121.111.2",
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    
    if origin in allowed_origins or origin == "*":
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Expose-Headers"] = "*"
    
    return response


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with CORS support"""
    
    @app.exception_handler(AppException)
    async def api_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle custom API exceptions"""
        logger.warning(f"APIException: {exc.msg}")
        response = JSONResponse(
            status_code=exc.status_code,
            content=APIResponse(
                code=exc.code,
                msg=exc.msg,
                data=None
            ).model_dump(),
        )
        return _add_cors_headers(response, request)
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions"""
        logger.warning(f"HTTPException: {exc.detail}")
        response = JSONResponse(
            status_code=exc.status_code,
            content=APIResponse(
                code=exc.status_code,
                msg=exc.detail,
                data=None
            ).model_dump(),
        )
        return _add_cors_headers(response, request)
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all uncaught exceptions"""
        logger.exception(f"Unhandled exception: {str(exc)}")
        response = JSONResponse(
            status_code=500,
            content=APIResponse(
                code=500,
                msg="Internal server error",
                data=None
            ).model_dump(),
        )
        return _add_cors_headers(response, request) 