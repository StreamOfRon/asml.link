"""Structured request logging middleware for audit trails and debugging."""

import json
import uuid
import time
from datetime import datetime
from quart import Request, Response, has_request_context, g
from app.config import settings


async def setup_request_logging(app):
    """Setup request logging middleware on Quart app.

    Args:
        app: Quart application instance
    """

    @app.before_request
    async def before_request():
        """Generate request ID and log incoming request."""
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        g.request_id = request_id
        g.start_time = time.time()

        from quart import request

        # Log request (avoid logging sensitive data)
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", "Unknown"),
        }

        # Only log in debug mode or for important endpoints
        if settings.debug or request.path.startswith("/api/admin"):
            app.logger.info(f"Request started: {json.dumps(log_data)}")

    @app.after_request
    async def after_request(response: Response):
        """Log response and request completion."""
        if not has_request_context():
            return response

        from quart import request

        # Calculate request duration
        start_time = getattr(g, "start_time", None)
        duration = None
        if start_time:
            duration = time.time() - start_time

        request_id = getattr(g, "request_id", "unknown")

        # Log response
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": int(duration * 1000) if duration else None,
        }

        # Only log in debug mode or for important endpoints
        if settings.debug or request.path.startswith("/api/admin"):
            app.logger.info(f"Request completed: {json.dumps(log_data)}")

        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id

        return response

    @app.errorhandler(Exception)
    async def handle_exception(error: Exception):
        """Log unhandled exceptions."""
        request_id = getattr(g, "request_id", "unknown") if has_request_context() else "unknown"

        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
        }

        app.logger.error(f"Unhandled exception: {json.dumps(error_data)}", exc_info=True)

        # Re-raise so Quart's error handlers can process it
        raise


def get_request_id() -> str:
    """Get the current request ID.

    Returns:
        The request ID for the current request, or 'unknown' if not in request context
    """
    if has_request_context():
        return getattr(g, "request_id", "unknown")
    return "unknown"
