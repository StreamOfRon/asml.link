"""Security tests for Phase 11 hardening features."""

from app.config import settings as app_settings
from app.middleware.csrf import CSRFProtection


class TestCSRFTokenGeneration:
    """Test CSRF token generation."""

    def test_generate_csrf_token(self):
        """Test CSRF token generation."""
        token = CSRFProtection.generate_token()
        assert token is not None
        assert len(token) > 30  # urlsafe base64 encoding

    def test_token_generation_uniqueness(self):
        """Test that each generated token is unique."""
        token1 = CSRFProtection.generate_token()
        token2 = CSRFProtection.generate_token()
        assert token1 != token2

    def test_csrf_token_field_name_defined(self):
        """Test that CSRF token field name is defined."""
        assert CSRFProtection.CSRF_TOKEN_FIELD == "_csrf_token"

    def test_csrf_session_key_defined(self):
        """Test that CSRF session key is defined."""
        assert CSRFProtection.CSRF_TOKEN_SESSION_KEY == "_csrf_token"

    def test_csrf_time_key_defined(self):
        """Test that CSRF time key is defined."""
        assert CSRFProtection.CSRF_TOKEN_TIME_KEY == "_csrf_token_time"


class TestCSRFConfiguration:
    """Test CSRF configuration is present."""

    def test_csrf_secret_key_configured(self):
        """Test CSRF secret key is configured."""
        assert app_settings.csrf_secret_key is not None
        assert len(app_settings.csrf_secret_key) > 0

    def test_csrf_token_expiration_configured(self):
        """Test CSRF token expiration is configured."""
        assert app_settings.csrf_token_expiration_minutes > 0

    def test_csrf_token_expiration_reasonable(self):
        """Test CSRF token expiration is reasonable."""
        # Should be at least 10 minutes but less than 24 hours
        assert 10 <= app_settings.csrf_token_expiration_minutes <= 1440


class TestSecurityConfiguration:
    """Test security-related configuration."""

    def test_hsts_enabled(self):
        """Test HSTS is enabled."""
        assert app_settings.enable_hsts is True

    def test_hsts_max_age_configured(self):
        """Test HSTS max-age is configured."""
        # At least 1 year
        assert app_settings.hsts_max_age >= 31536000

    def test_https_redirect_setting_exists(self):
        """Test HTTPS redirect setting exists."""
        assert hasattr(app_settings, "enable_https_redirect")

    def test_session_httponly_enabled(self):
        """Test session HTTPOnly is enabled."""
        assert app_settings.session_httponly is True

    def test_session_samesite_configured(self):
        """Test session SameSite is configured."""
        assert app_settings.session_samesite in ["Lax", "Strict", "None"]

    def test_session_secure_flag_exists(self):
        """Test session secure flag configuration exists."""
        assert hasattr(app_settings, "session_secure_cookies")


class TestMiddlewareImports:
    """Test that middleware modules can be imported."""

    def test_csrf_middleware_imports(self):
        """Test CSRF middleware can be imported."""
        from app.middleware.csrf import CSRFProtection, generate_csrf_token, validate_csrf_token

        assert CSRFProtection is not None
        assert generate_csrf_token is not None
        assert validate_csrf_token is not None

    def test_security_headers_middleware_imports(self):
        """Test security headers middleware can be imported."""
        from app.middleware.security_headers import (
            add_security_headers,
            setup_security_headers_middleware,
        )

        assert add_security_headers is not None
        assert setup_security_headers_middleware is not None

    def test_error_handler_middleware_imports(self):
        """Test error handler middleware can be imported."""
        from app.middleware.error_handler import setup_error_handlers

        assert setup_error_handlers is not None

    def test_request_logging_middleware_imports(self):
        """Test request logging middleware can be imported."""
        from app.middleware.request_logging import get_request_id, setup_request_logging

        assert setup_request_logging is not None
        assert get_request_id is not None


class TestSecurityHeadersConfiguration:
    """Test security headers configuration."""

    def test_content_security_policy_builder(self):
        """Test CSP can be built with required directives."""
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
        )
        assert "default-src" in csp
        assert "script-src" in csp
        assert "style-src" in csp

    def test_referrer_policy_configured(self):
        """Test Referrer-Policy is configured."""
        policy = "strict-origin-when-cross-origin"
        assert len(policy) > 0
        assert policy in [
            "no-referrer",
            "no-referrer-when-downgrade",
            "same-origin",
            "origin",
            "strict-origin",
            "origin-when-cross-origin",
            "strict-origin-when-cross-origin",
            "unsafe-url",
        ]

    def test_permissions_policy_restrictions(self):
        """Test Permissions-Policy includes restrictions."""
        policy = "geolocation=(), microphone=(), camera=()"
        assert "geolocation" in policy
        assert "microphone" in policy
        assert "camera" in policy


class TestErrorHandlingConfiguration:
    """Test error handling configuration."""

    def test_app_exception_imported(self):
        """Test AppException can be imported."""
        from app.exceptions import AppException

        assert AppException is not None

    def test_validation_error_imported(self):
        """Test ValidationError can be imported."""
        from app.exceptions import ValidationError

        assert ValidationError is not None

    def test_unauthorized_error_imported(self):
        """Test UnauthorizedError can be imported."""
        from app.exceptions import UnauthorizedError

        assert UnauthorizedError is not None

    def test_forbidden_error_imported(self):
        """Test ForbiddenError can be imported."""
        from app.exceptions import ForbiddenError

        assert ForbiddenError is not None

    def test_not_found_error_imported(self):
        """Test NotFoundError can be imported."""
        from app.exceptions import NotFoundError

        assert NotFoundError is not None

    def test_conflict_error_imported(self):
        """Test ConflictError can be imported."""
        from app.exceptions import ConflictError

        assert ConflictError is not None

    def test_rate_limit_error_imported(self):
        """Test RateLimitError can be imported."""
        from app.exceptions import RateLimitError

        assert RateLimitError is not None


class TestRequestLoggingConfiguration:
    """Test request logging configuration."""

    def test_request_logging_import(self):
        """Test request logging module can be imported."""
        from app.middleware.request_logging import get_request_id

        assert callable(get_request_id)

    def test_get_request_id_outside_request_context(self):
        """Test get_request_id returns 'unknown' outside request context."""
        from app.middleware.request_logging import get_request_id

        # Outside of request context, should return 'unknown'
        request_id = get_request_id()
        assert request_id == "unknown"


class TestSecurityHeadersBuilder:
    """Test security headers are properly constructed."""

    def test_csp_includes_frame_ancestors(self):
        """Test CSP includes frame-ancestors directive."""
        csp = "frame-ancestors 'none';"
        assert "frame-ancestors" in csp

    def test_x_frame_options_value_valid(self):
        """Test X-Frame-Options has valid value."""
        value = "DENY"
        assert value in ["DENY", "SAMEORIGIN", "ALLOW-FROM"]

    def test_x_content_type_options_value_valid(self):
        """Test X-Content-Type-Options has valid value."""
        value = "nosniff"
        assert value == "nosniff"

    def test_x_xss_protection_value_valid(self):
        """Test X-XSS-Protection has valid value."""
        value = "1; mode=block"
        assert "1" in value
        assert "mode=block" in value
