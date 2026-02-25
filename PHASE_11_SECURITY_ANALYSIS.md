# Phase 11 Security Hardening - Codebase Analysis

**Date:** February 24, 2026  
**Project:** asml.link (Python Link Shortening Service)  
**Framework:** Quart (Async Web Framework)  
**Total LOC:** ~3,900 lines

---

## 1. CURRENT PROJECT STRUCTURE

### Main Directories and Purposes:

```
/home/rmiller/Work/asml.link/
├── app/                          # Main application package
│   ├── __init__.py              # Quart app factory and initialization
│   ├── config.py                # Settings management (Pydantic)
│   ├── db.py                    # Database engine and session setup
│   ├── dependencies.py          # Dependency injection for services
│   ├── exceptions.py            # Custom exception hierarchy
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── link.py
│   │   ├── oauth_account.py
│   │   ├── allow_list_entry.py
│   │   └── rate_limit_entry.py
│   ├── routes/                  # Blueprint route handlers
│   │   ├── web.py              # HTML template routes (web UI)
│   │   ├── links.py            # Link API endpoints (CRUD)
│   │   ├── users.py            # User management API (admin)
│   │   ├── redirect.py         # URL shortcut redirect handler
│   │   ├── dashboard.py        # Dashboard API endpoints
│   │   └── allowlist.py        # Allow-list management API
│   ├── services/                # Business logic layer
│   │   ├── link_service.py
│   │   ├── user_service.py
│   │   ├── auth_service.py
│   │   ├── rate_limiter.py
│   │   └── stats_service.py
│   ├── schemas/                 # Pydantic validation schemas
│   │   ├── link.py
│   │   ├── user.py
│   │   └── dashboard.py
│   ├── utils/                   # Utility functions
│   │   ├── validators.py       # Input validation helpers
│   │   ├── token_manager.py    # JWT token operations
│   │   ├── oauth.py            # OAuth2 provider integration
│   │   └── slug_generator.py   # URL slug generation
│   ├── middleware/              # Custom middleware (EMPTY)
│   ├── static/                  # CSS/JS assets
│   │   ├── css/custom.css
│   │   └── js/main.js
│   └── templates/               # Jinja2 HTML templates
│       ├── base.html
│       ├── login.html
│       ├── dashboard.html
│       ├── admin/
│       └── errors/
├── migrations/                  # Alembic database migrations
├── tests/                       # Pytest test suite (110 tests passing)
├── run.py                       # Development server entry point
├── pyproject.toml               # Project dependencies & config
├── docker-compose.yaml
└── Dockerfile
```

### Key Observations:
- **No middleware directory implementation** - middleware folder exists but is empty
- **Web routes use session** - `/app/routes/web.py` uses Quart's `session` for user authentication
- **API routes lack authentication** - API endpoints check for `None` user_id (placeholder)
- **Plugin architecture ready** - Blueprints registered in app factory allow for easy module addition

---

## 2. WEB FRAMEWORK & VERSIONS

**Framework:** Quart v0.18.0+  
**ASGI Server Support:** Hypercorn/Uvicorn recommended for production

### Key Dependencies:
```
quart>=0.18.0           # Async web framework (Flask-compatible)
sqlalchemy>=2.0         # Async ORM with connection pooling
authlib>=1.2.0          # OAuth2 provider support
pyjwt>=2.8.0            # JWT token generation/validation
pydantic>=2.0           # Data validation
pydantic-settings>=2.0  # Configuration management
aiohttp>=3.9.0          # Async HTTP client (for OAuth)
aiosqlite>=0.19.0       # Async SQLite driver
alembic>=1.12.0         # Database migrations
python-dotenv>=1.0.0    # Environment variable loading
```

**Python:** >=3.10 required

---

## 3. EXISTING MIDDLEWARE, ERROR HANDLERS & SECURITY UTILITIES

### Error Handlers (in `app/__init__.py`):
```python
@app.errorhandler(404)
async def handle_404(error) -> tuple[dict, int]:
    """Handle 404 Not Found errors."""
    return jsonify({"error": "Not found", "message": str(error)}), 404

@app.errorhandler(500)
async def handle_500(error) -> tuple[dict, int]:
    """Handle 500 Internal Server Error."""
    app.logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500
```

**Status:** Minimal. Only 404 and 500 handlers exist.

### Custom Exception Hierarchy (`app/exceptions.py`):
- `AppException` - Base exception with status_code
- `ValidationError` - 400 status
- `NotFoundError` - 404 status
- `UnauthorizedError` - 401 status
- `ForbiddenError` - 403 status
- `ConflictError` - 409 status
- `RateLimitError` - 429 status

**Status:** Well-structured, ready for use.

### Security Utilities:
**Location:** `app/utils/validators.py`
- `is_valid_url()` - Validates URLs (scheme, netloc, max 2048 chars)
- `is_valid_email()` - RFC 5322 simplified regex validation
- `normalize_email()` - Lowercase and strip whitespace
- `is_valid_full_name()` - Optional name validation

**Status:** Basic, needs expansion for CSRF token validation and XSS prevention.

### Middleware Status:
- **File:** `/app/middleware/` directory exists but is **EMPTY**
- **Current middleware:** Only using Quart's built-in session middleware via `session` object
- **Missing:** No custom middleware for authentication, CSRF protection, security headers, rate limiting, logging

---

## 4. FORMS/ROUTES NEEDING CSRF PROTECTION

### HTML Forms (Template-Based Routes):

**Web Routes (`app/routes/web.py`):**
1. **Login Page** - `/login` (GET) - OAuth login (no traditional form)
2. **Logout** - `/logout` (GET) - Session clear
3. **Dashboard** - `/dashboard` (GET/POST via AJAX)
   - Profile update form (email, full_name, avatar_url)
   - Link management (likely AJAX-based)
4. **Admin Dashboard** - `/admin` (GET)
5. **Admin Users Page** - `/admin/users` (GET)
6. **Admin Allow-list Page** - `/admin/allow-list` (GET)

**Dashboard JavaScript (`app/templates/dashboard.html`):**
```html
<form id="profile-form" onsubmit="updateProfile(event)">
    <input type="text" id="full_name" value="{{ current_user.full_name or '' }}">
    <input type="url" id="avatar_url" value="{{ current_user.avatar_url or '' }}">
</form>
```

### API Routes Accepting Data (Need CSRF for web forms, but not API tokens):

**POST/PATCH/DELETE routes:**
- `POST /api/links` - Create link (LinkCreateRequest)
- `PATCH /api/links/<id>` - Update link (LinkUpdateRequest)
- `DELETE /api/links/<id>` - Delete link
- `POST /api/admin/allow-list` - Add to allow-list (AllowListAddRequest)
- `DELETE /api/admin/allow-list/<email>` - Remove from allow-list
- `PATCH /api/users/<id>/admin` - Toggle admin status
- `PATCH /api/users/<id>/block` - Toggle block status
- `DELETE /api/users/<id>` - Delete user

**Status:** 
- Web routes use AJAX but **NO CSRF tokens implemented**
- API routes lack authentication middleware (checking None for user_id)
- Session-based authentication vulnerable to CSRF

---

## 5. CURRENT INPUT VALIDATION

### Schema-Based Validation (Pydantic):

**Link Creation (`app/schemas/link.py`):**
```python
class LinkCreateRequest(BaseModel):
    original_url: str = Field(..., min_length=1, max_length=2048)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    is_public: bool = Field(True)
    allowed_emails: Optional[list[str]] = Field(None)
```

**Link Update:**
```python
class LinkUpdateRequest(BaseModel):
    original_url: Optional[str] = Field(None, min_length=1, max_length=2048)
    is_public: Optional[bool] = Field(None)
    allowed_emails: Optional[list[str]] = Field(None)
```

**User Update (`app/schemas/user.py`):**
```python
class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = Field(None, min_length=1, max_length=512)
```

**Allow-list (`app/schemas/user.py`):**
```python
class AllowListAddRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
```

### Utility Validators (`app/utils/validators.py`):
```python
def is_valid_url(url: str, max_length: int = 2048) -> bool
def is_valid_email(email: str, max_length: int = 255) -> bool
def normalize_email(email: str) -> str
def is_valid_full_name(name: Optional[str], max_length: int = 255) -> bool
```

### Validation in Routes:
- Pydantic schemas catch JSON parsing errors
- Manual email validation using `is_valid_email()` and `normalize_email()`
- Pagination validation: `if page < 1 or page_size < 1 or page_size > 100`
- Query parameters validated with `request.args.get(..., type=int)`

**Status:**
- ✅ **Good:** Pydantic schemas with length constraints
- ✅ **Good:** Email format validation
- ✅ **Good:** URL validation with scheme/netloc checks
- ⚠️ **Missing:** 
  - SQL injection protection (relying on SQLAlchemy ORM, good)
  - XSS prevention (templates need escaping verification)
  - HTML sanitization for user input
  - Rate limiting validation details

---

## 6. LOGGING SYSTEMS IN PLACE

### Current Logging Implementation:

**Using Quart's built-in logger:**
```python
from quart import current_app

# Error logging
current_app.logger.error(f"Error creating link: {str(e)}")
current_app.logger.info(f"Link not found for slug: {slug}")
current_app.logger.warning(f"Public link access check failed for slug: {slug}")
```

**Locations used in:**
- `app/routes/links.py` - 5 error logs
- `app/routes/redirect.py` - 6 logs (info, warning, error)
- `app/routes/users.py` - 5 error logs
- `app/routes/allowlist.py` - 3 error logs
- `app/__init__.py` - 1 error log

**Configuration:**
```python
# From config.py
log_level: str = Field(default="INFO")
```

**Status:**
- ✅ **Good:** Using Quart's logger (integrates with ASGI server)
- ⚠️ **Limitations:**
  - No structured logging (JSON format)
  - No request ID tracking
  - No audit logging for sensitive operations
  - No log rotation configured
  - No separate audit log file

---

## 7. CURRENT SECURITY HEADERS

### Status: **NOT IMPLEMENTED**

No security headers are currently being set. The application is missing:

**Missing Headers:**
- ❌ `Content-Security-Policy` (CSP)
- ❌ `X-Content-Type-Options: nosniff`
- ❌ `X-Frame-Options: SAMEORIGIN`
- ❌ `X-XSS-Protection: 1; mode=block`
- ❌ `Strict-Transport-Security` (HSTS)
- ❌ `Referrer-Policy`
- ❌ `Permissions-Policy` (Feature Policy)
- ❌ `Access-Control-Allow-*` (CORS headers)

**Implementation Point:**
Middleware should be added to `app/middleware/` to inject these headers on all responses.

---

## 8. MAIN APP INITIALIZATION CODE

**File:** `app/__init__.py`

```python
async def create_app() -> Quart:
    """Create and configure the Quart application."""
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
    async def handle_404(error) -> tuple[dict, int]:
        """Handle 404 Not Found errors."""
        return jsonify({"error": "Not found", "message": str(error)}), 404

    @app.errorhandler(500)
    async def handle_500(error) -> tuple[dict, int]:
        """Handle 500 Internal Server Error."""
        app.logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500

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
    app.register_blueprint(redirect_bp)  # Last to not interfere

    # Health check endpoint
    @app.route("/health")
    async def health_check() -> tuple[dict, int]:
        """Health check endpoint for load balancers."""
        return jsonify({"status": "healthy"}), 200

    return app
```

**Entry Point:** `run.py`
```python
async def main():
    """Create and run the application."""
    app = await create_app()
    return app

app = asyncio.run(main())

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
```

**Key Pattern:** App factory pattern allows for flexible initialization and testing.

---

## 9. AUTH/SESSION MANAGEMENT IN PLACE

### Session Management:

**Method:** Quart's built-in session support (server-side or signed client cookies)
```python
# From web.py
async def get_current_user():
    """Get current user from session."""
    if "user_id" in session:
        db = await get_db()
        service = UserService(db)
        user = await service.get_user(session["user_id"])
        return user
    return None
```

**Login/Logout:**
```python
@web_bp.route("/logout")
async def logout():
    """Logout endpoint - clear session and redirect to login."""
    session.clear()
    return redirect("/login")
```

**Status:**
- ⚠️ **Incomplete:** Session stored in memory (not production-ready)
- ⚠️ **No configuration:** Session secret not explicitly configured
- ✅ **OAuth paths:** OAuth flows are prepared but incomplete

### JWT Token Management:

**File:** `app/utils/token_manager.py`

```python
class TokenManager:
    @staticmethod
    def create_access_token(user_id: int, email: str, is_admin: bool = False) -> str:
        """Create an access token for a user."""
        # Uses PyJWT with configured secret key and algorithm
        # Expires in JWT_EXPIRATION_SECONDS (default 3600)
        
    @staticmethod
    def create_refresh_token(user_id: int, email: str) -> str:
        """Create a refresh token for a user."""
        # Longer expiration: REFRESH_TOKEN_EXPIRATION_DAYS (default 7)
        
    @staticmethod
    def verify_token(token: str) -> Optional[TokenPayload]:
        """Verify and decode a JWT token."""
        # Returns None if expired or invalid
        
    @staticmethod
    def create_tokens(user_id: int, email: str, is_admin: bool = False) -> Dict[str, str]:
        """Create both access and refresh tokens."""
```

**Token Payload:**
```python
class TokenPayload:
    user_id: int
    email: str
    is_admin: bool
    token_type: str  # 'access' or 'refresh'
```

**Configuration:**
```python
jwt_secret_key: str = Field(default="dev-secret-key-change-in-production")
jwt_algorithm: str = Field(default="HS256")
jwt_expiration_seconds: int = Field(default=3600)  # 1 hour
refresh_token_expiration_days: int = Field(default=7)
```

### OAuth2 Integration:

**File:** `app/utils/oauth.py`

```python
class OAuthProvider:
    """OAuth2 provider client for authorization, token exchange, and user info."""
    
    # Supports: Google, GitHub (pluggable)
    
    async def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        
    async def get_user_info(access_token: str) -> OAuthUserInfo:
        """Retrieve user information from OAuth provider."""

class OAuthUserInfo:
    provider_id: str      # User ID at provider
    email: Optional[str]  # Email address
    name: Optional[str]   # Full name
    avatar_url: Optional[str]
    provider: str         # 'google' or 'github'
```

**Auth Service:**
```python
class AuthService:
    async def link_oauth_account(...) -> OAuthAccount:
        """Link OAuth account to user."""
        
    async def get_or_create_user_from_oauth(...) -> tuple[User, bool]:
        """Get existing user or create new from OAuth."""
        
    async def update_oauth_tokens(...) -> OAuthAccount:
        """Update OAuth tokens for user."""
```

**Status:**
- ✅ **Good:** JWT implementation ready
- ✅ **Good:** OAuth2 provider abstraction prepared
- ⚠️ **Incomplete:** 
  - No authentication middleware to check JWT tokens on API routes
  - Placeholder in routes: `user_id = None  # Placeholder - will be extracted from JWT`
  - Web routes use session but API routes don't validate auth

---

## CURRENT SECURITY POSTURE SUMMARY

### ✅ STRENGTHS:
1. **Async/ASGI Architecture** - Inherently safer than sync frameworks for concurrency
2. **ORM-Based Queries** - SQLAlchemy prevents SQL injection
3. **Pydantic Validation** - Strong schema validation with length constraints
4. **Custom Exception Hierarchy** - Proper error handling structure
5. **Structured Auth Service** - OAuth and JWT infrastructure ready
6. **Rate Limiting Service** - Implemented with time windows
7. **User Models** - Includes is_admin and is_blocked flags
8. **Dependency Injection** - Services cleanly separated

### ⚠️ CRITICAL GAPS (For Phase 11):
1. **NO CSRF Protection** - Forms use AJAX but no tokens
2. **NO Security Headers** - Missing Content-Security-Policy, X-Frame-Options, etc.
3. **NO Auth Middleware** - API routes lack JWT/session verification
4. **NO HTTPS Enforcement** - No Strict-Transport-Security, redirects
5. **NO Request ID Tracking** - Limited audit trail capability
6. **NO XSS Prevention** - No Content-Security-Policy, no HTML sanitization
7. **NO CORS Configuration** - No Access-Control headers
8. **NO Rate Limiting Middleware** - Service exists but not applied to routes
9. **NO Structured Logging** - Basic logging only, no audit trail
10. **NO Input Sanitization** - No HTML/JavaScript filtering

### 🔧 MISSING MIDDLEWARE:
- Authentication middleware (JWT verification)
- CSRF protection middleware
- Security headers middleware
- Rate limiting middleware
- Request logging/audit middleware
- Error handling middleware
- CORS middleware
- Request ID injection middleware

---

## PHASE 11 IMPLEMENTATION STRATEGY

### Files to Create:
```
app/middleware/
├── __init__.py
├── auth.py              # JWT token verification
├── csrf.py              # CSRF token generation/validation
├── security_headers.py  # Inject security headers
├── rate_limit.py        # Rate limiting enforcement
├── request_logging.py   # Structured logging with request IDs
└── error_handler.py     # Centralized error handling
```

### Existing Patterns to Follow:
1. **Blueprint Registration:** Follow the pattern in `app/__init__.py`
2. **Service Layer:** Use pattern from `app/services/auth_service.py`
3. **Exception Handling:** Use custom exceptions from `app/exceptions.py`
4. **Configuration:** Add settings to `app/config.py` (Pydantic-based)
5. **Validation:** Add helper functions to `app/utils/validators.py`
6. **Logging:** Use `current_app.logger` (already in use)

### Configuration Additions Needed:
```python
# In app/config.py
csrf_key: str = Field(default="...")  # CSRF token secret
csrf_token_expiry: int = Field(default=3600)  # 1 hour
secure_cookies: bool = Field(default=False)  # Set to True in production
http_only_cookies: bool = Field(default=True)
same_site_cookies: str = Field(default="Lax")
cors_origins: str = Field(default="*")  # Comma-separated
cors_allow_credentials: bool = Field(default=True)
trust_proxy: bool = Field(default=False)  # For real IP extraction
```

---

## NOTES FOR SECURITY IMPLEMENTATION

### Route Pattern Recognition:
- **Web routes** (`/`, `/login`, `/dashboard`, `/admin*`) - Need CSRF + Session
- **API routes** (`/api/*`) - Need JWT + Rate limiting + Security headers
- **Redirect route** (`/<slug>`) - Public, light validation only

### Session vs JWT Strategy:
- **Web UI (HTML forms):** Use signed session cookies + CSRF tokens
- **API endpoints:** Use Bearer JWT tokens in Authorization header
- **Status page:** `/health` - No auth required

### Security Headers Application:
- All routes should receive standard headers (Content-Security-Policy, X-Frame-Options, etc.)
- API endpoints may need different CSP (no script-src for JSON responses)
- Consider using middleware to apply globally

### Logging for Compliance:
- User login/logout events
- Admin actions (promote/demote, block/unblock, delete user)
- Link creation/deletion
- Allow-list modifications
- Authentication failures
- Rate limit violations

---

**End of Analysis**
