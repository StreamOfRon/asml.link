"""API route blueprints."""

from app.routes.links import links_bp
from app.routes.redirect import redirect_bp

__all__ = ["links_bp", "redirect_bp"]
