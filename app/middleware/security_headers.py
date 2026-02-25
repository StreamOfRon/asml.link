"""Security headers middleware for adding security-related HTTP headers."""

from quart import Response
from app.config import settings


async def add_security_headers(response: Response) -> Response:
    """Add security headers to response.

    Args:
        response: The response object to add headers to

    Returns:
        Response with security headers added
    """
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Enable XSS protection (legacy, but still useful)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Feature policy / Permissions policy
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )

    # HTTP Strict Transport Security (HSTS)
    if settings.enable_hsts:
        hsts_value = f"max-age={settings.hsts_max_age}; includeSubDomains"
        if not settings.debug:
            hsts_value += "; preload"
        response.headers["Strict-Transport-Security"] = hsts_value

    # Remove server identification
    response.headers["Server"] = "Application"

    return response


async def setup_security_headers_middleware(app):
    """Setup security headers middleware on Quart app.

    Args:
        app: Quart application instance
    """

    @app.after_request
    async def after_request(response):
        return await add_security_headers(response)
