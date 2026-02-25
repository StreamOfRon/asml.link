"""Quart application factory and initialization.

This module creates and configures the Quart application instance,
setting up middleware, error handlers, and route blueprints.
"""

from quart import Quart, jsonify
from quart.exceptions import HTTPException

from app.config import settings
from app.models import init_db, close_db


async def create_app() -> Quart:
    """Create and configure the Quart application.

    Returns:
        Configured Quart application instance.
    """
    app = Quart(__name__)

    # Configuration
    app.config["JSON_SORT_KEYS"] = False

    # Startup and shutdown handlers
    @app.before_serving
    async def startup() -> None:
        """Initialize database on startup."""
        await init_db()

    @app.after_serving
    async def shutdown() -> None:
        """Close database connections on shutdown."""
        await close_db()

    # Error handlers
    @app.errorhandler(404)
    async def handle_404(error: HTTPException) -> tuple[dict, int]:
        """Handle 404 Not Found errors."""
        return jsonify({"error": "Not found", "message": str(error)}), 404

    @app.errorhandler(500)
    async def handle_500(error: HTTPException) -> tuple[dict, int]:
        """Handle 500 Internal Server Error."""
        app.logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    # Register blueprints (will be added in future phases)
    # from app.routes import auth_bp, links_bp, users_bp, admin_bp
    # app.register_blueprint(auth_bp)
    # app.register_blueprint(links_bp)
    # app.register_blueprint(users_bp)
    # app.register_blueprint(admin_bp)

    # Health check endpoint
    @app.route("/health")
    async def health_check() -> tuple[dict, int]:
        """Health check endpoint for load balancers."""
        return jsonify({"status": "healthy"}), 200

    return app
