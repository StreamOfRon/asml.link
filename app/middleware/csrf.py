"""CSRF protection middleware for preventing cross-site request forgery attacks."""

import secrets
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

from quart import request, session, current_app
from app.config import settings


class CSRFProtection:
    """CSRF protection utility for generating and validating tokens."""

    CSRF_TOKEN_FIELD = "_csrf_token"
    CSRF_TOKEN_SESSION_KEY = "_csrf_token"
    CSRF_TOKEN_TIME_KEY = "_csrf_token_time"

    @staticmethod
    def generate_token() -> str:
        """Generate a new CSRF token.

        Returns:
            A cryptographically secure random CSRF token
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    async def validate_token(token: Optional[str]) -> bool:
        """Validate a CSRF token from request.

        Args:
            token: The CSRF token to validate (from form or header)

        Returns:
            True if token is valid, False otherwise
        """
        if not token:
            return False

        # Get token from session
        session_token = session.get(CSRFProtection.CSRF_TOKEN_SESSION_KEY)
        if not session_token:
            return False

        # Check if token matches
        if not hmac.compare_digest(token, session_token):
            return False

        # Check if token has expired
        token_time = session.get(CSRFProtection.CSRF_TOKEN_TIME_KEY)
        if not token_time:
            return False

        try:
            token_datetime = datetime.fromisoformat(token_time)
            expiration = timedelta(minutes=settings.csrf_token_expiration_minutes)
            if datetime.utcnow() - token_datetime > expiration:
                return False
        except (ValueError, TypeError):
            return False

        return True

    @staticmethod
    async def get_or_create_token() -> str:
        """Get existing CSRF token from session or create a new one.

        Returns:
            A CSRF token string
        """
        token = session.get(CSRFProtection.CSRF_TOKEN_SESSION_KEY)

        if not token:
            token = CSRFProtection.generate_token()
            session[CSRFProtection.CSRF_TOKEN_SESSION_KEY] = token
            session[CSRFProtection.CSRF_TOKEN_TIME_KEY] = datetime.utcnow().isoformat()

        return token

    @staticmethod
    async def inject_token_to_template(template_context: dict) -> dict:
        """Inject CSRF token into template context.

        Args:
            template_context: Template context dictionary

        Returns:
            Updated template context with CSRF token
        """
        token = await CSRFProtection.get_or_create_token()
        template_context[CSRFProtection.CSRF_TOKEN_FIELD] = token
        return template_context


async def generate_csrf_token() -> str:
    """Helper function to generate CSRF token.

    Returns:
        A new CSRF token
    """
    return await CSRFProtection.get_or_create_token()


async def validate_csrf_token(token: Optional[str] = None) -> bool:
    """Helper function to validate CSRF token.

    Args:
        token: The CSRF token to validate. If None, attempts to get from request.

    Returns:
        True if token is valid, False otherwise
    """
    if token is None:
        # Try to get token from form data
        form_data = await request.form
        token = form_data.get(CSRFProtection.CSRF_TOKEN_FIELD)

        # Try to get token from JSON body
        if not token:
            try:
                json_data = await request.get_json()
                if isinstance(json_data, dict):
                    token = json_data.get(CSRFProtection.CSRF_TOKEN_FIELD)
            except Exception:
                pass

        # Try to get token from headers (for AJAX)
        if not token:
            token = request.headers.get("X-CSRFToken")

    return await CSRFProtection.validate_token(token)


async def require_csrf_protection(func):
    """Decorator to require CSRF protection on a route.

    Args:
        func: The route handler function

    Returns:
        Wrapped function that validates CSRF token before proceeding
    """

    async def wrapper(*args, **kwargs):
        # Skip CSRF validation for safe methods
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return await func(*args, **kwargs)

        # Validate CSRF token
        if not await validate_csrf_token():
            from app.exceptions import ForbiddenError

            raise ForbiddenError("Invalid CSRF token")

        return await func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
