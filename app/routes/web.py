"""Web template routes for serving HTML pages.

This module provides routes for rendering Jinja2 templates and handling
page navigation for the link shortener web interface.
"""

from quart import Blueprint, render_template, request, redirect, session, g
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.services.link_service import LinkService
from app.services.user_service import UserService
from app.services.stats_service import StatsService

web_bp = Blueprint("web", __name__)


# Helper function to get current user from session
async def get_current_user():
    """Get current user from session.

    Returns:
        User object if authenticated, None otherwise
    """
    if "user_id" in session:
        db = await get_db()
        service = UserService(db)
        user = await service.get_user(session["user_id"])
        return user
    return None


# Public routes


@web_bp.route("/")
async def home():
    """Home page - redirect to dashboard if logged in, else to login."""
    current_user = await get_current_user()

    if current_user:
        return redirect("/dashboard")
    return redirect("/login")


@web_bp.route("/login")
async def login():
    """Login page with OAuth provider options."""
    current_user = await get_current_user()

    if current_user:
        return redirect("/dashboard")

    return await render_template("login.html", current_user=current_user)


@web_bp.route("/logout")
async def logout():
    """Logout endpoint - clear session and redirect to login."""
    session.clear()
    return redirect("/login")


# Protected user routes


@web_bp.route("/dashboard")
async def dashboard():
    """User dashboard page."""
    current_user = await get_current_user()

    if not current_user:
        return redirect("/login")

    # Get user's links and stats
    db = await get_db()
    link_service = LinkService(db)
    stats_service = StatsService(db)

    links = await link_service.get_user_links(current_user.id)
    total_links = len(links)
    total_hits = sum(link.hit_count for link in links)
    avg_hits = (total_hits // total_links) if total_links > 0 else 0

    return await render_template(
        "dashboard.html",
        current_user=current_user,
        links=links,
        total_links=total_links,
        total_hits=total_hits,
        avg_hits=avg_hits,
        request=request,
    )


# Protected admin routes


@web_bp.route("/admin")
async def admin_dashboard():
    """Admin dashboard page."""
    current_user = await get_current_user()

    if not current_user:
        return redirect("/login")

    if not current_user.is_admin:
        return await render_template("errors/403.html", current_user=current_user), 403

    # Get admin dashboard data
    db = await get_db()
    stats_service = StatsService(db)
    user_service = UserService(db)
    link_service = LinkService(db)

    # Get statistics
    total_users = await stats_service.get_total_users()
    total_links = await stats_service.get_total_links()
    total_hits = await stats_service.get_total_hits()
    active_users = await stats_service.get_active_users_count()
    admin_count = await stats_service.get_admin_count()
    blocked_count = await stats_service.get_blocked_users_count()
    public_links_count = await stats_service.get_public_links_count()
    private_links_count = await stats_service.get_private_links_count()

    # Get recent data
    recent_users = await user_service.get_recent_users(limit=5)
    recent_links = await link_service.get_recent_links(limit=5)

    return await render_template(
        "admin/dashboard.html",
        current_user=current_user,
        total_users=total_users,
        total_links=total_links,
        total_hits=total_hits,
        active_users=active_users,
        admin_count=admin_count,
        blocked_count=blocked_count,
        public_links_count=public_links_count,
        private_links_count=private_links_count,
        recent_users=recent_users,
        recent_links=recent_links,
    )


@web_bp.route("/admin/users")
async def admin_users():
    """Admin user management page."""
    current_user = await get_current_user()

    if not current_user:
        return redirect("/login")

    if not current_user.is_admin:
        return await render_template("errors/403.html", current_user=current_user), 403

    # Get all users
    db = await get_db()
    user_service = UserService(db)
    users = await user_service.get_all_users()

    return await render_template(
        "admin/users.html",
        current_user=current_user,
        users=users,
    )


@web_bp.route("/admin/allow-list")
async def admin_allowlist():
    """Admin allow-list management page."""
    current_user = await get_current_user()

    if not current_user:
        return redirect("/login")

    if not current_user.is_admin:
        return await render_template("errors/403.html", current_user=current_user), 403

    # Get allow-list entries
    db = await get_db()

    # TODO: Implement allow-list service or directly query from db
    from app.models import AllowlistEntry
    from sqlalchemy import select

    result = await db.execute(select(AllowlistEntry).order_by(AllowlistEntry.created_at.desc()))
    allow_list = result.scalars().all()

    return await render_template(
        "admin/allowlist.html",
        current_user=current_user,
        allow_list=allow_list,
    )


# Error handlers


@web_bp.errorhandler(401)
async def handle_401(error):
    """Handle 401 Unauthorized errors."""
    current_user = await get_current_user()
    return await render_template("errors/401.html", current_user=current_user), 401


@web_bp.errorhandler(403)
async def handle_403(error):
    """Handle 403 Forbidden errors."""
    current_user = await get_current_user()
    return await render_template("errors/403.html", current_user=current_user), 403


@web_bp.errorhandler(404)
async def handle_404(error):
    """Handle 404 Not Found errors."""
    current_user = await get_current_user()
    return await render_template("errors/404.html", current_user=current_user), 404


@web_bp.errorhandler(500)
async def handle_500(error):
    """Handle 500 Internal Server Error."""
    current_user = await get_current_user()
    return await render_template("errors/500.html", current_user=current_user), 500
