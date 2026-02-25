"""Slug generation utilities for shortened URLs."""

import random
import string

# Base62 character set (0-9, a-z, A-Z)
BASE62_CHARS = string.digits + string.ascii_lowercase + string.ascii_uppercase


def generate_random_slug(length: int = 6) -> str:
    """Generate a random Base62 slug for a shortened URL.

    Args:
        length: Length of the slug (default 6 characters)

    Returns:
        A random alphanumeric slug

    Raises:
        ValueError: If length is less than 1
    """
    if length < 1:
        raise ValueError("Slug length must be at least 1")

    return "".join(random.choice(BASE62_CHARS) for _ in range(length))


def validate_slug(slug: str) -> bool:
    """Validate that a slug contains only Base62 characters.

    Args:
        slug: The slug to validate

    Returns:
        True if valid, False otherwise
    """
    if not slug or len(slug) == 0:
        return False

    return all(c in BASE62_CHARS for c in slug)


def is_valid_slug_length(slug: str, min_length: int = 1, max_length: int = 255) -> bool:
    """Check if slug length is within acceptable bounds.

    Args:
        slug: The slug to check
        min_length: Minimum length (default 1)
        max_length: Maximum length (default 255)

    Returns:
        True if length is valid, False otherwise
    """
    return min_length <= len(slug) <= max_length
