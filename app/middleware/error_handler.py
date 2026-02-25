"""Global error handling middleware for centralized exception processing."""

import json
from typing import Optional
from quart import Request, Response, jsonify, render_template
from werkzeug.exceptions import HTTPException

from app.exceptions import (
    AppException,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    RateLimitError,
)


async def setup_error_handlers(app):
    """Setup global error handlers for the application.

    Args:
        app: Quart application instance
    """

    @app.errorhandler(AppException)
    async def handle_app_exception(error: AppException):
        """Handle custom application exceptions."""
        response_data = {
            "error": error.__class__.__name__,
            "message": str(error),
        }

        if error.details:
            response_data["details"] = error.details

        response = jsonify(response_data)
        response.status_code = error.status_code
        return response

    @app.errorhandler(ValidationError)
    async def handle_validation_error(error: ValidationError):
        """Handle validation errors."""
        response_data = {
            "error": "ValidationError",
            "message": str(error),
        }

        if error.details:
            response_data["details"] = error.details

        response = jsonify(response_data)
        response.status_code = 400
        return response

    @app.errorhandler(UnauthorizedError)
    async def handle_unauthorized_error(error: UnauthorizedError):
        """Handle unauthorized errors."""
        response_data = {
            "error": "UnauthorizedError",
            "message": str(error),
        }

        response = jsonify(response_data)
        response.status_code = 401
        return response

    @app.errorhandler(ForbiddenError)
    async def handle_forbidden_error(error: ForbiddenError):
        """Handle forbidden errors."""
        response_data = {
            "error": "ForbiddenError",
            "message": str(error),
        }

        response = jsonify(response_data)
        response.status_code = 403
        return response

    @app.errorhandler(NotFoundError)
    async def handle_not_found_error(error: NotFoundError):
        """Handle not found errors."""
        response_data = {
            "error": "NotFoundError",
            "message": str(error),
        }

        response = jsonify(response_data)
        response.status_code = 404
        return response

    @app.errorhandler(ConflictError)
    async def handle_conflict_error(error: ConflictError):
        """Handle conflict errors."""
        response_data = {
            "error": "ConflictError",
            "message": str(error),
        }

        response = jsonify(response_data)
        response.status_code = 409
        return response

    @app.errorhandler(RateLimitError)
    async def handle_rate_limit_error(error: RateLimitError):
        """Handle rate limit errors."""
        response_data = {
            "error": "RateLimitError",
            "message": str(error),
        }

        if error.details:
            response_data["details"] = error.details

        response = jsonify(response_data)
        response.status_code = 429
        return response

    @app.errorhandler(404)
    async def handle_not_found(error):
        """Handle 404 Not Found errors."""
        # Check if it's an API request
        if _is_api_request():
            return jsonify({"error": "NotFound", "message": "Resource not found"}), 404

        return await render_template("404.html"), 404

    @app.errorhandler(500)
    async def handle_internal_error(error):
        """Handle 500 Internal Server Error."""
        app.logger.error(f"Internal server error: {error}", exc_info=True)

        # Check if it's an API request
        if _is_api_request():
            return (
                jsonify({"error": "InternalServerError", "message": "An error occurred"}),
                500,
            )

        return await render_template("500.html"), 500

    @app.errorhandler(HTTPException)
    async def handle_http_exception(error: HTTPException):
        """Handle HTTP exceptions."""
        if _is_api_request():
            return (
                jsonify({"error": error.__class__.__name__, "message": error.description}),
                error.code,
            )

        return await render_template(f"{error.code}.html"), error.code


def _is_api_request() -> bool:
    """Check if the current request is an API request.

    Returns:
        True if the request appears to be an API request, False otherwise
    """
    from quart import request

    # Check Accept header
    accept_header = request.headers.get("Accept", "")
    if "application/json" in accept_header:
        return True

    # Check request path
    if request.path.startswith("/api/"):
        return True

    return False
