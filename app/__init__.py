"""Quart application factory and initialization.

This module creates and configures the Quart application instance,
setting up middleware, error handlers, and route blueprints.
"""

from quart import Quart, jsonify

from app.config import settings
from app.models import init_db, close_db
from app.middleware import (
    setup_error_handlers,
    setup_request_logging,
    setup_security_headers_middleware,
)


async def create_app() -> Quart:
    """Create and configure the Quart application.

    Returns:
        Configured Quart application instance.
    """
    app = Quart(__name__)

    # Configuration
    app.config["JSON_SORT_KEYS"] = False
    app.config["SESSION_COOKIE_SECURE"] = settings.session_secure_cookies
    app.config["SESSION_COOKIE_HTTPONLY"] = settings.session_httponly
    app.config["SESSION_COOKIE_SAMESITE"] = settings.session_samesite
    app.secret_key = settings.csrf_secret_key

    # Startup and shutdown handlers
    @app.before_serving
    async def startup() -> None:
        """Initialize database on startup."""
        await init_db()

    @app.after_serving
    async def shutdown() -> None:
        """Close database connections on shutdown."""
        await close_db()

    # Setup global error handlers and middleware
    await setup_error_handlers(app)
    await setup_request_logging(app)
    await setup_security_headers_middleware(app)

    # Register blueprints
    from app.routes import (
        links_bp,
        redirect_bp,
        users_bp,
        allowlist_bp,
        admin_dashboard_bp,
        user_dashboard_bp,
        web_bp,
    )

    app.register_blueprint(web_bp)
    app.register_blueprint(links_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(allowlist_bp)
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(user_dashboard_bp)
    # Register redirect blueprint last so it doesn't interfere with other routes
    app.register_blueprint(redirect_bp)

    # Health check endpoint
    @app.route("/health")
    async def health_check() -> tuple[dict, int]:
        """Health check endpoint for load balancers."""
        return jsonify({"status": "healthy"}), 200

    return app
