"""API route blueprints."""

from app.routes.links import links_bp
from app.routes.redirect import redirect_bp
from app.routes.users import users_bp
from app.routes.allowlist import allowlist_bp
from app.routes.dashboard import admin_dashboard_bp, user_dashboard_bp

__all__ = [
    "links_bp",
    "redirect_bp",
    "users_bp",
    "allowlist_bp",
    "admin_dashboard_bp",
    "user_dashboard_bp",
]
