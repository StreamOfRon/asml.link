"""User management API route handlers (admin only)."""

from quart import Blueprint, jsonify, request, current_app

from app.models import get_db
from app.services.user_service import UserService
from app.schemas.user import UserResponse, UserListResponse, UserUpdateRequest
from app.exceptions import NotFoundError, ValidationError, AppException

# Create blueprint
users_bp = Blueprint("users", __name__, url_prefix="/api/users")


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


@users_bp.route("", methods=["GET"])
async def list_users():
    """List all users (admin only).

    Query parameters:
        page: int - Page number (default: 1)
        page_size: int - Items per page (default: 20)

    Returns:
        UserListResponse with paginated users

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

        # Get pagination params
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)

        # Validate pagination
        if page < 1 or page_size < 1 or page_size > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400

        # TODO: Implement proper pagination with SQLAlchemy
        # For now, get all users and slice them
        stmt = "SELECT * FROM users"  # Placeholder
        # users = await service.get_all_users()

        # Temporary: Return empty list (full implementation in Phase 8)
        response = UserListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
        )

        return jsonify(response.model_dump(mode="json")), 200

    except Exception as e:
        current_app.logger.error(f"Error listing users: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@users_bp.route("/<int:user_id>", methods=["GET"])
async def get_user(user_id: int):
    """Get user details (admin only).

    Path parameters:
        user_id: int - User ID

    Returns:
        UserResponse with user details

    Status codes:
        200 - Success
        401 - Unauthorized
        403 - Forbidden
        404 - User not found
    """
    try:
        # Check admin access
        current_user_id = get_current_user_id()
        if current_user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        db = await get_db()
        user_service = UserService(db)

        if not await check_admin_access(user_service, current_user_id):
            return jsonify({"error": "Forbidden", "message": "Admin access required"}), 403

        # Get user
        user = await user_service.get_user(user_id)
        if user is None:
            return jsonify({"error": "User not found"}), 404

        response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            is_admin=user.is_admin,
            is_blocked=user.is_blocked,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        return jsonify(response.model_dump(mode="json")), 200

    except Exception as e:
        current_app.logger.error(f"Error getting user: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@users_bp.route("/<int:user_id>/admin", methods=["PATCH"])
async def toggle_admin(user_id: int):
    """Toggle admin status for a user (admin only).

    Path parameters:
        user_id: int - User ID

    Query parameters:
        action: str - "promote" or "demote" (required)

    Returns:
        UserResponse with updated user

    Status codes:
        200 - Success
        400 - Invalid action
        401 - Unauthorized
        403 - Forbidden
        404 - User not found
    """
    try:
        # Check admin access
        current_user_id = get_current_user_id()
        if current_user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        db = await get_db()
        user_service = UserService(db)

        if not await check_admin_access(user_service, current_user_id):
            return jsonify({"error": "Forbidden", "message": "Admin access required"}), 403

        # Get action
        action = request.args.get("action", "").lower()
        if action not in ("promote", "demote"):
            return jsonify({"error": "Invalid action. Use 'promote' or 'demote'"}), 400

        # Perform action
        if action == "promote":
            user = await user_service.promote_to_admin(user_id)
        else:
            user = await user_service.demote_from_admin(user_id)

        response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            is_admin=user.is_admin,
            is_blocked=user.is_blocked,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        return jsonify(response.model_dump(mode="json")), 200

    except NotFoundError as e:
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        current_app.logger.error(f"Error toggling admin status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@users_bp.route("/<int:user_id>/block", methods=["PATCH"])
async def toggle_block(user_id: int):
    """Toggle blocked status for a user (admin only).

    Path parameters:
        user_id: int - User ID

    Query parameters:
        action: str - "block" or "unblock" (required)

    Returns:
        UserResponse with updated user

    Status codes:
        200 - Success
        400 - Invalid action
        401 - Unauthorized
        403 - Forbidden
        404 - User not found
    """
    try:
        # Check admin access
        current_user_id = get_current_user_id()
        if current_user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        db = await get_db()
        user_service = UserService(db)

        if not await check_admin_access(user_service, current_user_id):
            return jsonify({"error": "Forbidden", "message": "Admin access required"}), 403

        # Get action
        action = request.args.get("action", "").lower()
        if action not in ("block", "unblock"):
            return jsonify({"error": "Invalid action. Use 'block' or 'unblock'"}), 400

        # Perform action
        if action == "block":
            user = await user_service.block_user(user_id)
        else:
            user = await user_service.unblock_user(user_id)

        response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            is_admin=user.is_admin,
            is_blocked=user.is_blocked,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        return jsonify(response.model_dump(mode="json")), 200

    except NotFoundError as e:
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        current_app.logger.error(f"Error toggling block status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@users_bp.route("/<int:user_id>", methods=["DELETE"])
async def delete_user(user_id: int):
    """Delete a user (admin only).

    Path parameters:
        user_id: int - User ID

    Status codes:
        204 - User deleted successfully
        401 - Unauthorized
        403 - Forbidden
        404 - User not found
    """
    try:
        # Check admin access
        current_user_id = get_current_user_id()
        if current_user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        db = await get_db()
        user_service = UserService(db)

        if not await check_admin_access(user_service, current_user_id):
            return jsonify({"error": "Forbidden", "message": "Admin access required"}), 403

        # Delete user
        await user_service.delete_user(user_id)

        return jsonify({}), 204

    except NotFoundError as e:
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting user: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
