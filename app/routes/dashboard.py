"""Dashboard API routes for admin and user dashboards."""

from quart import Blueprint, jsonify, request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.link import Link
from app.services.stats_service import StatsService
from app.services.user_service import UserService

# Create blueprints
admin_dashboard_bp = Blueprint("admin_dashboard", __name__, url_prefix="/api/admin/dashboard")
user_dashboard_bp = Blueprint("user_dashboard", __name__, url_prefix="/api/user/dashboard")


# Placeholder for getting current user ID from auth context
async def get_current_user_id() -> int:
    """Get current user ID from auth context.

    TODO: Implement JWT token extraction

    Returns:
        Current user ID (placeholder: returns 1)
    """
    return 1


# Placeholder for checking admin access
async def check_admin_access(user_id: int, session: AsyncSession) -> bool:
    """Check if user has admin access.

    Args:
        user_id: User ID to check
        session: Database session

    Returns:
        True if user is admin, False otherwise
    """
    service = UserService(session)
    return await service.is_user_admin(user_id)


# Admin Dashboard Routes


@admin_dashboard_bp.route("", methods=["GET"])
async def get_admin_dashboard(db_session: AsyncSession):
    """Get admin dashboard with system statistics.

    Returns:
        Admin dashboard data with statistics and recent activity
    """
    # TODO: Implement JWT token extraction
    user_id = await get_current_user_id()

    if not await check_admin_access(user_id, db_session):
        return jsonify({"error": "Unauthorized"}), 403

    stats_service = StatsService(db_session)

    # Get system statistics
    total_users = await stats_service.get_total_users()
    total_links = await stats_service.get_total_links()
    total_hits = await stats_service.get_total_hits()
    active_users = await stats_service.get_active_users()
    public_links = await stats_service.get_public_links_count()
    private_links = await stats_service.get_private_links_count()

    stats = {
        "total_users": total_users,
        "total_links": total_links,
        "total_hits": total_hits,
        "active_users": active_users,
        "public_links": public_links,
        "private_links": private_links,
    }

    # Get recent activity (placeholder for now)
    recent_activity = []

    # Get system config
    system_config = {
        "instance_name": settings.INSTANCE_NAME,
        "allow_private_links_only": settings.ALLOW_PRIVATE_LINKS_ONLY,
        "enable_allow_list_mode": settings.ENABLE_ALLOW_LIST_MODE,
    }

    return (
        jsonify(
            {
                "stats": stats,
                "recent_activity": recent_activity,
                "system_config": system_config,
            }
        ),
        200,
    )


@admin_dashboard_bp.route("/config", methods=["GET"])
async def get_admin_config(db_session: AsyncSession):
    """Get instance configuration for admin dashboard.

    Returns:
        Instance configuration with admin statistics
    """
    # TODO: Implement JWT token extraction
    user_id = await get_current_user_id()

    if not await check_admin_access(user_id, db_session):
        return jsonify({"error": "Unauthorized"}), 403

    stats_service = StatsService(db_session)

    total_admins = await stats_service.get_total_admins()
    total_blocked = await stats_service.get_total_blocked_users()

    # Determine database type from connection URL
    db_url = settings.DATABASE_URL or ""
    if "postgresql" in db_url:
        db_type = "postgresql"
    else:
        db_type = "sqlite"

    return (
        jsonify(
            {
                "instance_name": settings.INSTANCE_NAME,
                "allow_private_links_only": settings.ALLOW_PRIVATE_LINKS_ONLY,
                "enable_allow_list_mode": settings.ENABLE_ALLOW_LIST_MODE,
                "total_admins": total_admins,
                "total_blocked_users": total_blocked,
                "database_type": db_type,
            }
        ),
        200,
    )


# User Dashboard Routes


@user_dashboard_bp.route("", methods=["GET"])
async def get_user_dashboard(db_session: AsyncSession):
    """Get user dashboard with personal statistics.

    Returns:
        User dashboard data with links and statistics
    """
    # TODO: Implement JWT token extraction
    user_id = await get_current_user_id()

    # Get user
    user_service = UserService(db_session)
    user = await user_service.get_user(user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    # Get user statistics
    stats_service = StatsService(db_session)
    total_links = await stats_service.get_user_link_count(user_id)
    total_hits = await stats_service.get_user_total_hits(user_id)

    return (
        jsonify(
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "total_links": total_links,
                "total_hits": total_hits,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        ),
        200,
    )


@user_dashboard_bp.route("/links", methods=["GET"])
async def get_user_links(db_session: AsyncSession):
    """Get user's links with pagination and statistics.

    Query Parameters:
        page: Page number (default: 1)
        page_size: Items per page (default: 10)

    Returns:
        Paginated list of user's links with statistics
    """
    # TODO: Implement JWT token extraction
    user_id = await get_current_user_id()

    # Get query parameters
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 10, type=int)

    # Validate pagination
    if page < 1 or page_size < 1 or page_size > 100:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    offset = (page - 1) * page_size

    # Get total count
    total_result = await db_session.execute(
        select(Link.__table__.c.id).where(Link.user_id == user_id)
    )
    total = len(total_result.fetchall())

    # Get paginated links
    result = await db_session.execute(
        select(Link)
        .where(Link.user_id == user_id)
        .order_by(desc(Link.created_at))
        .limit(page_size)
        .offset(offset)
    )
    links = result.scalars().all()

    # Format response
    links_data = [
        {
            "id": link.id,
            "slug": link.slug,
            "original_url": link.original_url,
            "is_public": link.is_public,
            "hit_count": link.hit_count,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "last_hit_at": link.last_hit_at.isoformat() if link.last_hit_at else None,
        }
        for link in links
    ]

    total_pages = (total + page_size - 1) // page_size

    return (
        jsonify(
            {
                "links": links_data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        ),
        200,
    )
