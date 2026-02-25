"""Link API route handlers."""

from quart import Blueprint, current_app, jsonify, request

from app.exceptions import (
    AppException,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import get_db
from app.schemas.link import (
    LinkCreateRequest,
    LinkListResponse,
    LinkResponse,
    LinkUpdateRequest,
)
from app.services.link_service import LinkService

# Create blueprint
links_bp = Blueprint("links", __name__, url_prefix="/api/links")


# Helper function to extract authenticated user
async def get_authenticated_user():
    """Get authenticated user from request context."""
    # This would be implemented with proper JWT/OAuth2 integration
    # For now, we'll return None to indicate unauthenticated
    # In Phase 6+, this will integrate with proper authentication middleware
    return None


@links_bp.route("", methods=["POST"])
async def create_link():
    """Create a new shortened link.

    Request body:
        original_url: str - Original URL to shorten
        slug: str (optional) - Custom slug
        is_public: bool - Whether link is publicly accessible (default: true)
        allowed_emails: list[str] (optional) - Allowed emails for private links

    Returns:
        LinkResponse with created link details

    Status codes:
        201 - Link created successfully
        400 - Invalid request data
        401 - User not authenticated
    """
    try:
        # Get user from auth context (TBD in Phase 6)
        user_id = None  # Placeholder - will be extracted from JWT token
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        # Parse and validate request
        try:
            data = await request.get_json()
        except Exception as e:
            return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

        try:
            req = LinkCreateRequest(**data)
        except ValueError as e:
            return jsonify({"error": f"Validation error: {str(e)}"}), 400

        # Get database session and service
        db = await get_db()
        service = LinkService(db)

        # Create link
        link = await service.create_link(
            user_id=user_id,
            original_url=req.original_url,
            slug=req.slug,
            is_public=req.is_public,
            allowed_emails=req.allowed_emails,
        )

        # Convert to response
        response = LinkResponse(
            id=link.id,
            user_id=link.user_id,
            original_url=link.original_url,
            slug=link.slug,
            is_public=link.is_public,
            allowed_emails=link.get_allowed_emails() if link.allowed_emails else None,
            hit_count=link.hit_count,
            last_hit_at=link.last_hit_at,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )

        return jsonify(response.model_dump(mode="json")), 201

    except AppException as e:
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error creating link: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@links_bp.route("", methods=["GET"])
async def list_links():
    """List links for authenticated user.

    Query parameters:
        page: int - Page number (default: 1)
        page_size: int - Items per page (default: 20)

    Returns:
        LinkListResponse with paginated links

    Status codes:
        200 - Success
        401 - User not authenticated
    """
    try:
        # Get user from auth context (TBD in Phase 6)
        user_id = None  # Placeholder - will be extracted from JWT token
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        # Get pagination params
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)

        # Validate pagination
        if page < 1 or page_size < 1 or page_size > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400

        # Get database session and service
        db = await get_db()
        service = LinkService(db)

        # Get user's links
        links = await service.get_user_links(user_id, include_private=True)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        paginated_links = links[start:end]

        # Convert to responses
        items = [
            LinkResponse(
                id=link.id,
                user_id=link.user_id,
                original_url=link.original_url,
                slug=link.slug,
                is_public=link.is_public,
                allowed_emails=link.get_allowed_emails() if link.allowed_emails else None,
                hit_count=link.hit_count,
                last_hit_at=link.last_hit_at,
                created_at=link.created_at,
                updated_at=link.updated_at,
            )
            for link in paginated_links
        ]

        response = LinkListResponse(
            items=items,
            total=len(links),
            page=page,
            page_size=page_size,
        )

        return jsonify(response.model_dump(mode="json")), 200

    except Exception as e:
        current_app.logger.error(f"Error listing links: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@links_bp.route("/<int:link_id>", methods=["GET"])
async def get_link(link_id: int):
    """Get a specific link by ID.

    Path parameters:
        link_id: int - Link ID

    Returns:
        LinkResponse with link details

    Status codes:
        200 - Success
        401 - User not authenticated
        403 - User doesn't own the link
        404 - Link not found
    """
    try:
        # Get user from auth context (TBD in Phase 6)
        user_id = None  # Placeholder - will be extracted from JWT token
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        # Get database session and service
        db = await get_db()
        service = LinkService(db)

        # Get link with permission check
        link = await service.get_link(link_id, user_id)

        # Convert to response
        response = LinkResponse(
            id=link.id,
            user_id=link.user_id,
            original_url=link.original_url,
            slug=link.slug,
            is_public=link.is_public,
            allowed_emails=link.get_allowed_emails() if link.allowed_emails else None,
            hit_count=link.hit_count,
            last_hit_at=link.last_hit_at,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )

        return jsonify(response.model_dump(mode="json")), 200

    except NotFoundError as e:
        return jsonify({"error": e.message}), 404
    except ForbiddenError as e:
        return jsonify({"error": e.message}), 403
    except Exception as e:
        current_app.logger.error(f"Error getting link: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@links_bp.route("/<int:link_id>", methods=["PATCH"])
async def update_link(link_id: int):
    """Update a link.

    Path parameters:
        link_id: int - Link ID

    Request body:
        original_url: str (optional) - Original URL
        is_public: bool (optional) - Public accessibility
        allowed_emails: list[str] (optional) - Allowed emails

    Returns:
        LinkResponse with updated link details

    Status codes:
        200 - Link updated successfully
        400 - Invalid request data
        401 - User not authenticated
        403 - User doesn't own the link
        404 - Link not found
    """
    try:
        # Get user from auth context (TBD in Phase 6)
        user_id = None  # Placeholder - will be extracted from JWT token
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        # Parse and validate request
        try:
            data = await request.get_json()
        except Exception as e:
            return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

        try:
            req = LinkUpdateRequest(**data)
        except ValueError as e:
            return jsonify({"error": f"Validation error: {str(e)}"}), 400

        # Get database session and service
        db = await get_db()
        service = LinkService(db)

        # Update link
        link = await service.update_link(
            link_id=link_id,
            user_id=user_id,
            original_url=req.original_url,
            is_public=req.is_public,
            allowed_emails=req.allowed_emails,
        )

        # Convert to response
        response = LinkResponse(
            id=link.id,
            user_id=link.user_id,
            original_url=link.original_url,
            slug=link.slug,
            is_public=link.is_public,
            allowed_emails=link.get_allowed_emails() if link.allowed_emails else None,
            hit_count=link.hit_count,
            last_hit_at=link.last_hit_at,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )

        return jsonify(response.model_dump(mode="json")), 200

    except NotFoundError as e:
        return jsonify({"error": e.message}), 404
    except ForbiddenError as e:
        return jsonify({"error": e.message}), 403
    except ValidationError as e:
        return jsonify({"error": e.message}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating link: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@links_bp.route("/<int:link_id>", methods=["DELETE"])
async def delete_link(link_id: int):
    """Delete a link.

    Path parameters:
        link_id: int - Link ID

    Status codes:
        204 - Link deleted successfully
        401 - User not authenticated
        403 - User doesn't own the link
        404 - Link not found
    """
    try:
        # Get user from auth context (TBD in Phase 6)
        user_id = None  # Placeholder - will be extracted from JWT token
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        # Get database session and service
        db = await get_db()
        service = LinkService(db)

        # Delete link
        await service.delete_link(link_id, user_id)

        return jsonify({}), 204

    except NotFoundError as e:
        return jsonify({"error": e.message}), 404
    except ForbiddenError as e:
        return jsonify({"error": e.message}), 403
    except Exception as e:
        current_app.logger.error(f"Error deleting link: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
