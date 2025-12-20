import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses"""

    async def dispatch(self, request: Request, call_next):
        # Log request start
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"

        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {client_host}"
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log successful response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"status_code={response.status_code} "
                f"process_time={process_time:.4f}s"
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={str(e)} process_time={process_time:.4f}s",
                exc_info=False
            )

            raise
