"""Redirect route handler for shortened links."""

from typing import Optional

from quart import Blueprint, redirect, current_app
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.services.link_service import LinkService
from app.exceptions import NotFoundError, ForbiddenError

# Create blueprint (no URL prefix - handles root-level routes)
redirect_bp = Blueprint("redirect", __name__)


def get_user_email_from_request(request=None) -> Optional[str]:
    """Extract user email from authenticated request context.

    This is a placeholder that will be integrated with JWT auth in Phase 7.
    For now, returns None to simulate unauthenticated requests.

    Args:
        request: Quart request object (optional, can use current_request if needed)

    Returns:
        User email if authenticated, None otherwise
    """
    # TODO: Extract from JWT token in request headers (Phase 7 - Authentication Middleware)
    return None


@redirect_bp.route("/<slug>", methods=["GET"])
async def redirect_to_link(slug: str):
    """Redirect to the original URL for a shortened link.

    Path parameters:
        slug: The shortened URL slug (Base62 format)

    Behavior:
        - Public links: Redirect anyone (200/301/302)
        - Private links without email allowlist: Redirect authenticated users (200/301/302)
        - Private links with email allowlist: Check user email and redirect if allowed
        - Unauthenticated access to private link: Return 401 (with login prompt in UI)
        - Authenticated but not in allowlist: Return 403 (forbidden)
        - Non-existent slug: Return 404

    Status codes:
        200 - Success (in tests, Quart may return different codes)
        301 - Moved Permanently (permanent redirect)
        302 - Found (temporary redirect)
        401 - Unauthorized (private link, not authenticated)
        403 - Forbidden (private link, not in allowlist)
        404 - Not Found (slug doesn't exist)

    Returns:
        Redirect response to original_url or error response
    """
    try:
        # Get database session and service
        db = await get_db()
        service = LinkService(db)

        # Lookup the link by slug
        link = await service.get_link_by_slug(slug)
        if link is None:
            current_app.logger.info(f"Link not found for slug: {slug}")
            return (
                {"error": "Link not found", "message": f"Shortened URL '/{slug}' does not exist."},
                404,
            )

        # Check access control
        user_email = get_user_email_from_request()
        can_access = await service.check_link_access(link, user_email=user_email)

        if not can_access:
            # Determine if user is authenticated
            if link.is_public:
                # Public link should always be accessible
                current_app.logger.warning(f"Public link access check failed for slug: {slug}")
                return (
                    {
                        "error": "Access Denied",
                        "message": "You do not have permission to access this link.",
                    },
                    403,
                )
            elif user_email is None:
                # Private link and user is not authenticated
                current_app.logger.info(f"Unauthenticated access attempt to private link: {slug}")
                return (
                    {
                        "error": "Unauthorized",
                        "message": "This link is private. Please log in to access it.",
                    },
                    401,
                )
            else:
                # Private link and user is authenticated but not in allowlist
                current_app.logger.info(
                    f"Forbidden access to private link for user {user_email}: {slug}"
                )
                return (
                    {
                        "error": "Forbidden",
                        "message": "You do not have permission to access this private link.",
                    },
                    403,
                )

        # Increment hit count
        try:
            await service.increment_hit_count(slug)
        except Exception as e:
            # Log error but don't fail the redirect
            current_app.logger.error(f"Error incrementing hit count for slug {slug}: {str(e)}")

        # Return redirect response
        # Use 302 (temporary) by default, allow config for 301 (permanent) in future
        return redirect(link.original_url, code=302)

    except Exception as e:
        current_app.logger.error(f"Error processing redirect for slug {slug}: {str(e)}")
        return (
            {"error": "Internal Server Error", "message": "An unexpected error occurred."},
            500,
        )
