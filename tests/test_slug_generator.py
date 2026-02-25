"""Unit tests for slug generation utilities."""

import pytest

from app.utils.slug_generator import (
    BASE62_CHARS,
    generate_random_slug,
    is_valid_slug_length,
    validate_slug,
)


class TestGenerateRandomSlug:
    """Test suite for random slug generation."""

    def test_generate_default_length(self):
        """Test that default slug generation creates 6-character slugs."""
        slug = generate_random_slug()
        assert len(slug) == 6

    def test_generate_custom_length(self):
        """Test slug generation with custom length."""
        for length in [1, 5, 10, 255]:
            slug = generate_random_slug(length=length)
            assert len(slug) == length

    def test_slug_contains_valid_characters(self):
        """Test that generated slugs only contain Base62 characters."""
        for _ in range(100):
            slug = generate_random_slug()
            assert all(c in BASE62_CHARS for c in slug)

    def test_slug_randomness(self):
        """Test that multiple slug generations produce different results."""
        slugs = {generate_random_slug() for _ in range(100)}
        # Should have at least 95% unique slugs in 100 generations
        assert len(slugs) > 95

    def test_invalid_length_raises_error(self):
        """Test that invalid lengths raise ValueError."""
        with pytest.raises(ValueError):
            generate_random_slug(length=0)

        with pytest.raises(ValueError):
            generate_random_slug(length=-1)


class TestValidateSlug:
    """Test suite for slug validation."""

    def test_valid_slugs(self):
        """Test that valid Base62 slugs pass validation."""
        valid_slugs = [
            "abc",
            "ABC123",
            "0123456789",
            "abcdefghijklmnopqrstuvwxyz",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "aA0bB1cC2",
        ]
        for slug in valid_slugs:
            assert validate_slug(slug) is True

    def test_invalid_characters(self):
        """Test that slugs with invalid characters fail validation."""
        invalid_slugs = [
            "hello-world",
            "hello_world",
            "hello.world",
            "hello world",
            "hello@world",
            "héllo",
            "hello!",
        ]
        for slug in invalid_slugs:
            assert validate_slug(slug) is False

    def test_empty_slug(self):
        """Test that empty slug fails validation."""
        assert validate_slug("") is False

    def test_none_slug(self):
        """Test that None slug fails validation."""
        assert validate_slug(None) is False


class TestIsValidSlugLength:
    """Test suite for slug length validation."""

    def test_valid_lengths(self):
        """Test valid slug lengths."""
        assert is_valid_slug_length("a") is True
        assert is_valid_slug_length("abc") is True
        assert is_valid_slug_length("a" * 255) is True

    def test_custom_bounds(self):
        """Test slug length validation with custom bounds."""
        assert is_valid_slug_length("ab", min_length=2, max_length=10) is True
        assert is_valid_slug_length("a", min_length=2, max_length=10) is False
        assert is_valid_slug_length("a" * 11, min_length=2, max_length=10) is False

    def test_edge_cases(self):
        """Test edge cases for slug length validation."""
        # Minimum length
        assert is_valid_slug_length("a", min_length=1, max_length=255) is True
        assert is_valid_slug_length("", min_length=1, max_length=255) is False

        # Maximum length
        assert is_valid_slug_length("a" * 255, min_length=1, max_length=255) is True
        assert is_valid_slug_length("a" * 256, min_length=1, max_length=255) is False
