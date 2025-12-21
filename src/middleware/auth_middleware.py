import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from src.services.auth_service import auth_service

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate Cognito JWT tokens for protected routes"""

    # Public routes that don't require authentication
    PUBLIC_ROUTES = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/chat/webhooks/twilio",  # Uses Twilio signature validation instead
    }

    def is_public_route(self, path: str) -> bool:
        """Check if a route is public"""
        # Exact match
        if path in self.PUBLIC_ROUTES:
            return True

        # Check if path starts with any public route
        for public_route in self.PUBLIC_ROUTES:
            if path.startswith(public_route):
                return True

        return False

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public routes
        if self.is_public_route(request.url.path):
            return await call_next(request)

        # Skip authentication for auth endpoints
        if request.url.path.startswith("/auth/"):
            return await call_next(request)

        # Extract token from Authorization header
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            logger.warning(
                f"Missing or invalid Authorization header for {request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = authorization.replace("Bearer ", "").strip()

        if not token:
            logger.warning(
                f"Empty token in Authorization header for {request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=401, content={"detail": "Missing access token"}
            )

        # Validate token
        try:
            await auth_service.validate_token(token)
            logger.debug(
                f"Token validated successfully for {request.method} {request.url.path}"
            )
        except ValueError as e:
            logger.warning(
                f"Token validation failed for {request.method} {request.url.path}: {str(e)}"
            )
            return JSONResponse(
                status_code=401, content={"detail": f"Invalid token: {str(e)}"}
            )
        except Exception as e:
            logger.error(
                f"Unexpected error validating token for {request.method} {request.url.path}: {str(e)}",
                exc_info=True,
            )
            return JSONResponse(
                status_code=500, content={"detail": "Internal server error"}
            )

        return await call_next(request)
