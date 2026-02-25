"""Input validation utilities."""

import re
from typing import Optional
from urllib.parse import urlparse


def is_valid_url(url: str, max_length: int = 2048) -> bool:
    """Validate that a URL is properly formatted.

    Args:
        url: The URL to validate
        max_length: Maximum URL length (default 2048)

    Returns:
        True if valid, False otherwise
    """
    if not url or len(url) > max_length:
        return False

    # Basic URL validation - check for scheme and netloc
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def is_valid_email(email: str, max_length: int = 255) -> bool:
    """Validate email format.

    Args:
        email: Email address to validate
        max_length: Maximum email length (default 255)

    Returns:
        True if valid, False otherwise
    """
    if not email or len(email) > max_length:
        return False

    # RFC 5322 simplified email regex
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def normalize_email(email: str) -> str:
    """Normalize email to lowercase.

    Args:
        email: Email to normalize

    Returns:
        Normalized email
    """
    return email.lower().strip()


def is_valid_full_name(name: Optional[str], max_length: int = 255) -> bool:
    """Validate full name format.

    Args:
        name: Full name to validate
        max_length: Maximum name length (default 255)

    Returns:
        True if valid (or None is acceptable), False otherwise
    """
    if name is None:
        return True  # Full name is optional

    if len(name) > max_length or len(name.strip()) == 0:
        return False

    return True
