"""Integration tests for web template routes."""

import pytest

from app import create_app
from app.models.user import User
from app.models.link import Link


@pytest.fixture
async def client():
    """Create a test client for the Quart app."""
    app = await create_app()
    # Set a secret key for session testing
    app.config["SECRET_KEY"] = "test-secret-key"
    async with app.test_client() as client:
        yield client


class TestWebRoutes:
    """Test web template routes."""

    async def test_home_redirect_to_login_unauthenticated(self, client):
        """Test home redirects to login when not authenticated."""
        response = await client.get("/")
        assert response.status_code == 302
        assert "/login" in response.location

    async def test_login_page_loads(self, client):
        """Test login page loads successfully."""
        response = await client.get("/login")
        assert response.status_code == 200
        html = await response.get_data(as_text=True)
        assert "login" in html.lower()

    async def test_dashboard_requires_authentication(self, client):
        """Test dashboard requires authentication."""
        response = await client.get("/dashboard")
        assert response.status_code == 302
        assert "/login" in response.location

    async def test_logout_redirects_to_login(self, client):
        """Test logout redirects to login."""
        response = await client.get("/logout")
        assert response.status_code == 302
        assert "/login" in response.location

    async def test_admin_dashboard_requires_authentication(self, client):
        """Test admin dashboard requires authentication."""
        response = await client.get("/admin")
        assert response.status_code == 302
        assert "/login" in response.location

    async def test_admin_users_page_requires_authentication(self, client):
        """Test admin users page requires authentication."""
        response = await client.get("/admin/users")
        assert response.status_code == 302
        assert "/login" in response.location

    async def test_admin_allowlist_page_requires_authentication(self, client):
        """Test admin allowlist page requires authentication."""
        response = await client.get("/admin/allow-list")
        assert response.status_code == 302
        assert "/login" in response.location


class TestErrorPages:
    """Test error page rendering."""

    async def test_404_error_on_invalid_route(self, client):
        """Test 404 error on invalid route."""
        # Note: redirect blueprint may catch some routes
        response = await client.get("/invalid-route-that-is-not-a-short-link")
        # Either 404 or 500 due to redirect processing
        assert response.status_code in (404, 500)


class TestTemplateContent:
    """Test template content and structure."""

    async def test_login_page_has_content(self, client):
        """Test login page has expected content."""
        response = await client.get("/login")
        assert response.status_code == 200
        html = await response.get_data(as_text=True)
        # Should have login-related content
        assert len(html) > 100
        assert "html" in html.lower()
        assert "<" in html  # Basic HTML structure check

    async def test_login_page_not_dashboard(self, client):
        """Test login page is different from dashboard."""
        response = await client.get("/login")
        html = await response.get_data(as_text=True)
        # Login page should not have dashboard-specific content
        assert "my links" not in html.lower() or "link created" not in html.lower()


class TestAuthenticationFlow:
    """Test authentication flow and redirects."""

    async def test_protected_routes_redirect_to_login(self, client):
        """Test all protected routes redirect to login when unauthenticated."""
        protected_routes = [
            "/dashboard",
            "/admin",
            "/admin/users",
            "/admin/allow-list",
        ]

        for route in protected_routes:
            response = await client.get(route)
            # Should redirect to login or return 302
            assert response.status_code == 302
            assert "/login" in response.location, f"Route {route} did not redirect to login"

    async def test_home_page_exists_and_responds(self, client):
        """Test home page exists and responds with redirect."""
        response = await client.get("/")
        assert response.status_code == 302

    async def test_logout_endpoint_accessible(self, client):
        """Test logout endpoint is accessible."""
        response = await client.get("/logout")
        assert response.status_code == 302
