"""Admin allow-list management API route handlers."""

from quart import Blueprint, current_app, jsonify, request
from sqlalchemy import select

from app.models import get_db
from app.models.allow_list_entry import AllowListEntry
from app.schemas.user import AllowListAddRequest, AllowListEntryResponse, AllowListResponse
from app.services.user_service import UserService
from app.utils.validators import is_valid_email, normalize_email

# Create blueprint
allowlist_bp = Blueprint("allowlist", __name__, url_prefix="/api/admin/allow-list")


def get_current_user_id() -> int | None:
    """Get authenticated user ID from request context.

    This is a placeholder that will be integrated with JWT auth in Phase 8+.
    For now, returns None to indicate unauthenticated.

    Returns:
        User ID if authenticated, None otherwise
    """
    # TODO: Extract from JWT token in request headers (Phase 8 - Authentication Middleware)
    return None


async def check_admin_access(user_service: UserService, user_id: int | None) -> bool:
    """Check if current user is admin.

    Args:
        user_service: UserService instance
        user_id: Current user's ID

    Returns:
        True if user is admin, False otherwise
    """
    if user_id is None:
        return False
    return await user_service.is_user_admin(user_id)


@allowlist_bp.route("", methods=["GET"])
async def list_allowlist():
    """List all emails in allow-list (admin only).

    Returns:
        AllowListResponse with list of allowed emails

    Status codes:
        200 - Success
        401 - Unauthorized (not authenticated)
        403 - Forbidden (not admin)
    """
    try:
        # Check admin access
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        db = await get_db()
        user_service = UserService(db)

        if not await check_admin_access(user_service, user_id):
            return jsonify({"error": "Forbidden", "message": "Admin access required"}), 403

        # Get all allow-list entries
        stmt = select(AllowListEntry).order_by(AllowListEntry.created_at.desc())
        result = await db.execute(stmt)
        entries = result.scalars().all()

        # Convert to responses
        items = [
            AllowListEntryResponse(
                email=entry.email,
                created_at=entry.created_at,
            )
            for entry in entries
        ]

        response = AllowListResponse(
            items=items,
            total=len(items),
        )

        return jsonify(response.model_dump(mode="json")), 200

    except Exception as e:
        current_app.logger.error(f"Error listing allow-list: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@allowlist_bp.route("", methods=["POST"])
async def add_to_allowlist():
    """Add email to allow-list (admin only).

    Request body:
        email: str - Email to add to allow-list

    Returns:
        AllowListEntryResponse with created entry

    Status codes:
        201 - Email added to allow-list
        400 - Invalid request
        401 - Unauthorized
        403 - Forbidden
        409 - Email already in allow-list
    """
    try:
        # Check admin access
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        db = await get_db()
        user_service = UserService(db)

        if not await check_admin_access(user_service, user_id):
            return jsonify({"error": "Forbidden", "message": "Admin access required"}), 403

        # Parse and validate request
        try:
            data = await request.get_json()
        except Exception as e:
            return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

        try:
            req = AllowListAddRequest(**data)
        except ValueError as e:
            return jsonify({"error": f"Validation error: {str(e)}"}), 400

        # Validate email
        if not is_valid_email(req.email):
            return jsonify({"error": f"Invalid email: {req.email}"}), 400

        email = normalize_email(req.email)

        # Check if already in allow-list
        stmt = select(AllowListEntry).where(AllowListEntry.email == email)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            return jsonify({"error": "Email already in allow-list"}), 409

        # Add to allow-list
        entry = AllowListEntry(email=email)
        db.add(entry)
        try:
            await db.commit()
            await db.refresh(entry)
        except Exception as e:
            await db.rollback()
            return jsonify({"error": f"Failed to add email: {str(e)}"}), 400

        response = AllowListEntryResponse(
            email=entry.email,
            created_at=entry.created_at,
        )

        return jsonify(response.model_dump(mode="json")), 201

    except Exception as e:
        current_app.logger.error(f"Error adding to allow-list: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@allowlist_bp.route("/<email>", methods=["DELETE"])
async def remove_from_allowlist(email: str):
    """Remove email from allow-list (admin only).

    Path parameters:
        email: str - Email to remove from allow-list

    Status codes:
        204 - Email removed from allow-list
        401 - Unauthorized
        403 - Forbidden
        404 - Email not in allow-list
    """
    try:
        # Check admin access
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        db = await get_db()
        user_service = UserService(db)

        if not await check_admin_access(user_service, user_id):
            return jsonify({"error": "Forbidden", "message": "Admin access required"}), 403

        # Normalize email
        normalized_email = normalize_email(email)

        # Find entry
        stmt = select(AllowListEntry).where(AllowListEntry.email == normalized_email)
        result = await db.execute(stmt)
        entry = result.scalar_one_or_none()

        if entry is None:
            return jsonify({"error": "Email not in allow-list"}), 404

        # Delete entry
        await db.delete(entry)
        await db.commit()

        return jsonify({}), 204

    except Exception as e:
        current_app.logger.error(f"Error removing from allow-list: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
