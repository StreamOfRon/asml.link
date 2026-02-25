"""Custom exceptions for the application."""


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(AppException):
    """Raised when data validation fails."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class UnauthorizedError(AppException):
    """Raised when user is not authenticated."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    """Raised when user lacks permissions."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class ConflictError(AppException):
    """Raised when operation conflicts with existing data."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)
