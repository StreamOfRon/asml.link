"""Unit tests for input validation utilities."""

from app.utils.validators import (
    is_valid_email,
    is_valid_full_name,
    is_valid_url,
    normalize_email,
)


class TestIsValidUrl:
    """Test suite for URL validation."""

    def test_valid_urls(self):
        """Test that valid URLs pass validation."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "https://example.com/path",
            "https://example.com/path?query=value",
            "https://subdomain.example.com",
            "https://example.com:8080",
        ]
        for url in valid_urls:
            assert is_valid_url(url) is True

    def test_invalid_urls(self):
        """Test that invalid URLs fail validation."""
        invalid_urls = [
            "",
            "not a url",
            "example.com",
            "ftp://example.com",
            "://example.com",
            "http://",
        ]
        for url in invalid_urls:
            assert is_valid_url(url) is False

    def test_url_max_length(self):
        """Test URL length validation."""
        # Valid URL under limit
        assert is_valid_url("https://example.com/path") is True

        # URL over default limit (2048)
        long_url = "https://example.com/" + "a" * 2050
        assert is_valid_url(long_url) is False

        # Custom max length
        assert is_valid_url("https://example.com/abc", max_length=30) is True
        assert is_valid_url("https://example.com/abcdefghijk", max_length=30) is False

    def test_none_url(self):
        """Test that None URL fails validation."""
        assert is_valid_url(None) is False


class TestIsValidEmail:
    """Test suite for email validation."""

    def test_valid_emails(self):
        """Test that valid emails pass validation."""
        valid_emails = [
            "user@example.com",
            "john.doe@example.com",
            "test+tag@example.co.uk",
            "user123@example.org",
            "a@b.co",
        ]
        for email in valid_emails:
            assert is_valid_email(email) is True

    def test_invalid_emails(self):
        """Test that invalid emails fail validation."""
        invalid_emails = [
            "",
            "not an email",
            "user@",
            "@example.com",
            "user@.com",
            "user @example.com",
            "user@example",
        ]
        for email in invalid_emails:
            assert is_valid_email(email) is False

    def test_email_max_length(self):
        """Test email length validation."""
        # Valid email under limit
        assert is_valid_email("user@example.com") is True

        # Email over default limit (255)
        long_email = "a" * 250 + "@example.com"
        assert is_valid_email(long_email) is False

    def test_none_email(self):
        """Test that None email fails validation."""
        assert is_valid_email(None) is False


class TestNormalizeEmail:
    """Test suite for email normalization."""

    def test_lowercase_conversion(self):
        """Test that emails are converted to lowercase."""
        assert normalize_email("User@Example.COM") == "user@example.com"
        assert normalize_email("JOHN.DOE@EXAMPLE.COM") == "john.doe@example.com"

    def test_whitespace_stripping(self):
        """Test that whitespace is stripped."""
        assert normalize_email("  user@example.com  ") == "user@example.com"
        assert normalize_email("\tuser@example.com\n") == "user@example.com"

    def test_combined_normalization(self):
        """Test combined normalization."""
        assert normalize_email("  USER@EXAMPLE.COM  ") == "user@example.com"


class TestIsValidFullName:
    """Test suite for full name validation."""

    def test_valid_names(self):
        """Test that valid names pass validation."""
        valid_names = [
            "John Doe",
            "Jane Smith",
            "Jean-Pierre Martin",
            "O'Brien",
            "José García",
        ]
        for name in valid_names:
            assert is_valid_full_name(name) is True

    def test_none_is_valid(self):
        """Test that None (optional) is valid."""
        assert is_valid_full_name(None) is True

    def test_empty_string_invalid(self):
        """Test that empty string is invalid."""
        assert is_valid_full_name("") is False
        assert is_valid_full_name("   ") is False

    def test_max_length(self):
        """Test name max length validation."""
        # Valid name under limit
        assert is_valid_full_name("John Doe") is True

        # Name over default limit (255)
        long_name = "a" * 256
        assert is_valid_full_name(long_name) is False

        # Custom max length
        assert is_valid_full_name("John", max_length=10) is True
        assert is_valid_full_name("John Doe Smith Jr.", max_length=10) is False
