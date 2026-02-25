# Python Link Shortening Application - Implementation Plan

## Project Overview

A Python-based link shortening service built with **Quart** async framework, featuring OAuth2 authentication, flexible access control, and comprehensive admin capabilities. The application supports both a REST API and web UI for managing shortened URLs with usage statistics.

## Technology Stack

- **Framework**: Quart (async web framework)
- **Database**: SQLAlchemy 2.0+ (async ORM) with PostgreSQL/SQLite support
- **Authentication**: OAuth2 with configurable providers
- **Session Management**: JWT tokens (stateless, scalable)
- **Frontend**: HTML/CSS/JavaScript with async API calls
- **Package Manager**: UV
- **Python Version**: 3.10+
- **Additional Libraries**: 
  - `authlib` or `python-jose` for OAuth2/JWT
  - `alembic` for database migrations
  - `pydantic` for validation
  - `python-dotenv` for configuration

---

## Application Architecture

```
shortlink-app/
├── app/
│   ├── __init__.py                 # Quart app factory
│   ├── config.py                   # Configuration management
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py                 # User model
│   │   ├── link.py                 # Link model
│   │   └── oauth_account.py        # OAuth provider accounts
│   ├── schemas/                    # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── link.py
│   │   ├── user.py
│   │   └── auth.py
│   ├── routes/                     # Route handlers
│   │   ├── __init__.py
│   │   ├── auth.py                 # OAuth login/logout
│   │   ├── links.py                # Link CRUD (API)
│   │   ├── redirect.py             # URL shortcut redirect
│   │   ├── users.py                # User management (admin)
│   │   └── admin.py                # Admin dashboard
│   ├── services/                   # Business logic
│   │   ├── __init__.py
│   │   ├── link_service.py         # Link creation/management
│   │   ├── auth_service.py         # OAuth/JWT handling
│   │   ├── user_service.py         # User management
│   │   └── stats_service.py        # Statistics tracking
│   ├── middleware/                 # Custom middleware
│   │   ├── __init__.py
│   │   ├── auth.py                 # JWT verification
│   │   └── error_handlers.py       # Global error handling
│   ├── templates/                  # Jinja2 templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── link_detail.html
│   │   ├── admin/
│   │   │   ├── users.html
│   │   │   └── links.html
│   │   └── 401.html / 403.html
│   ├── static/                     # CSS, JS, images
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── slug_generator.py       # Random slug generation
│       ├── validators.py           # Input validation
│       └── decorators.py           # Custom decorators
├── migrations/                     # Alembic database migrations
├── tests/                          # Test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_links.py
│   ├── test_redirect.py
│   └── test_admin.py
├── scripts/                        # Development scripts
│   ├── dev.sh                      # Start development server
│   ├── test.sh                     # Run tests with coverage
│   ├── lint.sh                     # Check code quality
│   └── format.sh                   # Auto-format code
├── .env.example                    # Configuration template
├── .gitignore
├── .pre-commit-config.yaml         # Pre-commit hooks configuration
├── pyproject.toml                  # UV project configuration
├── Dockerfile                      # Multi-stage Docker build
├── docker-compose.yaml             # Docker Compose development setup
├── .dockerignore
├── run.py                          # Application entry point
└── README.md
```

---

## Phase 1: Core Infrastructure & Authentication

### 1.1 Project Setup
- [ ] Initialize project structure with proper Python packaging
- [ ] Set up UV project management:
  - Create `pyproject.toml` with project metadata and dependencies
  - Target Python 3.10+ (requires-python = ">=3.10")
  - Configure UV for virtual environment management
  - Set up development and production dependency groups
  - Create `uv.lock` file (commit to version control)
- [ ] Create `.env.example` with template configuration variables
- [ ] Set up `.gitignore` (Python, environment files, IDE configs):
  - Add default development database: `shortlink.db`
- [ ] Configure pre-commit hooks (`.pre-commit-config.yaml`):
  - Ruff linting and formatting
  - Black code formatting
  - MyPy type checking
  - Trailing whitespace/end-of-file fixer
  - YAML formatting
- [ ] Create development scripts in `scripts/` directory:
  - `dev.sh` - Start development server with auto-reload
  - `test.sh` - Run test suite with coverage
  - `lint.sh` - Run all linting/formatting checks
  - `format.sh` - Auto-format code
- [ ] Set up Docker for development:
  - Create `Dockerfile` with multi-stage build (development and production)
  - Create `docker-compose.yaml` with app service only
  - Configure volume mounts for code hot-reloading
  - Set up environment variable passing from `.env`
  - App service uses SQLite database (`shortlink.db`) in development
- [ ] Document Docker development workflow:
  - `docker-compose --build up` to start development environment
  - Application automatically reloads on code changes
  - SQLite database persisted locally
- [ ] Create `config.py` with environment-based configuration:
  - Database connection string (default: `sqlite:///./shortlink.db` for development)
  - OAuth provider settings (client IDs, secrets, redirect URIs)
  - JWT secret key
  - Instance settings (allow private links only, allow-list mode, etc.)
  - Session/token expiration times

### 1.2 Database Layer
- [ ] Create SQLAlchemy models:
  - **User**: id, email, full_name, avatar_url, is_admin, is_blocked, created_at, updated_at
  - **Link**: id, user_id, original_url, slug, is_public, allowed_emails, created_at, updated_at, hit_count, last_hit_at
  - **OAuthAccount**: id, user_id, provider, provider_user_id, provider_email, access_token, refresh_token, created_at
  - **AllowListEntry**: id, email, created_at (for allow-list mode management)
- [ ] Set up Alembic for database migrations
- [ ] Create initial migration script
- [ ] Implement database initialization (with first user setup as admin)
- [ ] Add database utilities for common operations

### 1.3 OAuth2 Authentication
- [ ] Implement OAuth2 provider abstraction:
  - Support multiple configurable providers (Google, GitHub, Microsoft, etc.)
  - Dynamic provider registration from configuration
- [ ] Create OAuth routes:
  - `GET /auth/login/<provider>` - Redirects to OAuth provider
  - `GET /auth/callback/<provider>` - OAuth callback handler
  - `POST /auth/logout` - Logout endpoint
- [ ] Implement JWT token generation/validation:
  - Access token (short-lived)
  - Refresh token (long-lived)
  - Token storage in HTTP-only cookies
- [ ] Create auth service:
  - User registration on first OAuth login
  - User lookup/update on subsequent logins
  - First user auto-promotion to admin
  - Allow-list enforcement (if enabled)

---

## Phase 2: Link Management - Core Features

### 2.1 Link Creation & Management
- [ ] Implement link service:
  - Create shortened link with random slug (Base62)
  - Create shortened link with custom slug (with validation)
  - Slug uniqueness validation
  - Original URL validation
  - Enforce private-only mode (if configured)
- [ ] Create link routes (API + Web):
  - `POST /api/links` - Create new link (requires auth)
  - `GET /api/links` - List user's links (requires auth)
  - `GET /api/links/<id>` - Get link details (requires auth + ownership)
  - `PATCH /api/links/<id>` - Update link (requires auth + ownership)
  - `DELETE /api/links/<id>` - Delete link (requires auth + ownership)
  - `POST /links/create` - Web form for link creation (GET + POST)
- [ ] Implement access control decorator/middleware

### 2.2 Link Redirect Logic
- [ ] Create redirect route: `GET /<slug>` 
- [ ] Implement access control for private links:
  - Unauthenticated users → 401 with login option
  - Authenticated but unauthorized → 403 with explanation
  - Check allow-list mode for global access control
  - Check per-link email whitelist if applicable
- [ ] Implement statistics tracking:
  - Increment hit count
  - Update last_hit_at timestamp
- [ ] Implement proper redirect responses (301/302)

### 2.3 User Dashboard
- [ ] Create user dashboard route and template
- [ ] Display user's shortened links with:
  - Original URL, slug, creation date
  - Public/Private status
  - Hit count and last hit time
  - Quick edit/delete buttons
- [ ] Link management UI:
  - Create new link form
  - Edit link (URL, slug, access level, allowed emails)
  - Delete link with confirmation
  - Copy slug to clipboard

---

## Phase 3: Access Control & Permissions

### 3.1 Link Access Control
- [ ] Implement permission checking service:
  - Check link is public (anyone can access)
  - Check user is authenticated for private links
  - Check user email in allow-list (if set)
- [ ] Update redirect logic with comprehensive access control
- [ ] Error page templates for 401/403 with login option

### 3.2 User Management
- [ ] Implement user service for admin operations:
  - Fetch user list
  - Mark user as admin
  - Block/unblock user
  - Delete user (cascade delete user's links)
- [ ] Create user management routes (admin only):
  - `GET /api/users` - List all users (admin only)
  - `PATCH /api/users/<id>/admin` - Toggle admin status (admin only)
  - `PATCH /api/users/<id>/block` - Toggle blocked status (admin only)
  - `DELETE /api/users/<id>` - Delete user (admin only)

---

## Phase 4: Admin Dashboard & Features

### 4.1 Admin Dashboard Routes
- [ ] Create admin routes (admin-only middleware):
  - `GET /admin/` - Admin dashboard (overview stats)
  - `GET /admin/links` - View all links in system
  - `GET /admin/users` - View all users

### 4.2 Admin Dashboard UI
- [ ] Admin dashboard template showing:
  - System statistics (total links, total users, total hits)
  - Recent activity
  - Quick actions
- [ ] Admin links page:
  - Table of all links with user, original URL, slug, hit count
  - Edit/delete buttons for any link
  - Filter/search capabilities
- [ ] Admin users page:
  - Table of all users with email, creation date, admin status, blocked status
  - Buttons to toggle admin/blocked status
  - Delete user option

### 4.3 Instance Configuration Features
- [ ] Implement configuration options (via `.env`):
  - `REQUIRE_PRIVATE_LINKS_ONLY` - Force all links to be private
  - `ENABLE_ALLOW_LIST_MODE` - Only allow-listed emails can authenticate (enable/disable only via config)
- [ ] Create configuration validation on startup
- [ ] Create AllowListEntry model for database storage:
  - Store allowed emails for allow-list mode
  - Allow admin to add/remove emails at runtime
- [ ] Implement allow-list management routes (admin only):
  - `GET /api/admin/allow-list` - List allowed emails
  - `POST /api/admin/allow-list` - Add email to allow-list
  - `DELETE /api/admin/allow-list/<email>` - Remove email from allow-list
- [ ] Create allow-list management UI in admin dashboard:
  - Display current allowed emails
  - Form to add new emails
  - Delete buttons for existing entries
- [ ] Update auth service to check allow-list from database (if mode enabled)
- [ ] Add allow-list display in admin dashboard

---

## Phase 5: Statistics & Analytics

### 5.1 Statistics Service
- [ ] Implement statistics collection:
  - Track hit count per link
  - Track last hit timestamp per link
  - (Optional future: hourly/daily hit breakdown, geographic data, referrer tracking)
- [ ] Create statistics retrieval methods:
  - Get link statistics
  - Get user statistics (all their links' hits)
  - Get system statistics (admin only)

### 5.2 Statistics UI
- [ ] Display on user dashboard:
  - Hit count and last hit time per link
  - Total hits across all user's links
- [ ] Display on admin dashboard:
  - System-wide hit statistics
  - Top links
  - User activity trends

---

## Phase 6: Web UI & Templates

### 6.1 Base Layout & Navigation
- [ ] Create `base.html` template with:
  - Navigation bar with user info/logout
  - Login prompt for unauthenticated users
  - Responsive design
  - Error/success message area
- [ ] Create consistent styling (CSS framework or custom)

### 6.2 Authentication Pages
- [ ] Login page (`login.html`):
  - Display available OAuth providers dynamically
  - Provider buttons with icons
  - Redirect from unauthorized page (with return_to parameter)
- [ ] Create styled OAuth provider buttons

### 6.3 User-Facing Pages
- [ ] Dashboard (`dashboard.html`):
  - User's links list table
  - Create new link form/modal
  - Link statistics display
  - Edit/delete UI
- [ ] Link detail page (`link_detail.html`):
  - Show original URL and slug
  - Display QR code for shortened URL
  - Show access statistics
  - Edit form

### 6.4 Admin Pages
- [ ] Admin links page (`admin/links.html`):
  - Table of all system links
  - Search/filter functionality
  - Edit/delete buttons
- [ ] Admin users page (`admin/users.html`):
  - Table of all users
  - Admin/blocked status toggles
  - Delete user option
- [ ] Admin dashboard (`admin/dashboard.html`):
  - System overview statistics
  - Recent activity feed
  - Configuration display

### 6.5 Error Pages
- [ ] Create custom error templates:
  - `401.html` (Unauthenticated - with login button)
  - `403.html` (Forbidden - with explanation)
  - `404.html` (Not found)
  - `500.html` (Server error)

---

## Phase 7: API Development & REST Endpoints

### 7.1 Authentication API
- [ ] `GET /auth/login/<provider>` - Start OAuth flow
- [ ] `GET /auth/callback/<provider>` - OAuth callback
- [ ] `POST /auth/logout` - Logout
- [ ] `GET /auth/me` - Get current user info
- [ ] `POST /auth/refresh` - Refresh JWT token

### 7.2 Links API
- [ ] `POST /api/links` - Create link
  - Body: `{original_url, slug?, is_public?, allowed_emails?}`
  - Returns: full link object
- [ ] `GET /api/links` - List user's links (paginated)
- [ ] `GET /api/links/<id>` - Get link details
- [ ] `PATCH /api/links/<id>` - Update link
  - Can update: original_url, slug, is_public, allowed_emails
- [ ] `DELETE /api/links/<id>` - Delete link

### 7.3 Users API (Admin)
- [ ] `GET /api/users` - List all users (paginated, admin only)
- [ ] `GET /api/users/<id>` - Get user details (admin only)
- [ ] `PATCH /api/users/<id>/admin` - Toggle admin status (admin only)
- [ ] `PATCH /api/users/<id>/block` - Toggle blocked status (admin only)
- [ ] `DELETE /api/users/<id>` - Delete user (admin only)

### 7.4 Allow-List Management API (Admin)
- [ ] `GET /api/admin/allow-list` - List allowed emails (admin only)
- [ ] `POST /api/admin/allow-list` - Add email to allow-list (admin only)
  - Body: `{email}`
- [ ] `DELETE /api/admin/allow-list/<email>` - Remove email from allow-list (admin only)

### 7.5 Statistics API
- [ ] `GET /api/links/<id>/stats` - Get link statistics (owner or admin)
- [ ] `GET /api/stats/user` - Get user's overall statistics
- [ ] `GET /api/stats/system` - Get system statistics (admin only)

### 7.6 Admin API
- [ ] `GET /api/admin/dashboard` - Get dashboard data (admin only)
- [ ] `GET /api/admin/config` - Get instance configuration (admin only)

---

## Phase 8: Security & Error Handling

### 8.1 Security Measures
- [ ] Implement JWT validation middleware
- [ ] Implement admin-only route protection
- [ ] Implement ownership checks for link operations
- [ ] Implement CSRF protection for web forms
- [ ] Implement rate limiting on:
  - OAuth login attempts
  - Link creation (per user)
  - Link redirects (optional, per link)
- [ ] Input validation on all user inputs:
  - URL validation
  - Email validation
  - Slug format validation
- [ ] Secure password/token storage best practices

### 8.2 Error Handling
- [ ] Create global error handler middleware
- [ ] Implement custom exception classes:
  - `UnauthorizedError` (401)
  - `ForbiddenError` (403)
  - `NotFoundError` (404)
  - `ValidationError` (422)
  - `ConflictError` (409, e.g., slug exists)
- [ ] Return consistent error responses (JSON for API, HTML for web)
- [ ] Log errors appropriately

---

## Phase 9: Testing

### 9.1 Unit Tests
- [ ] Test slug generation (randomness, uniqueness, format)
- [ ] Test link service (CRUD operations, validation)
- [ ] Test authentication service (token generation, validation)
- [ ] Test user service (admin operations)
- [ ] Test access control logic

### 9.2 Integration Tests
- [ ] Test OAuth flow (with mocked OAuth provider)
- [ ] Test link creation and redirect flow
- [ ] Test private link access control
- [ ] Test admin operations
- [ ] Test API endpoints

### 9.3 End-to-End Tests
- [ ] Test complete user workflows (signup → create link → redirect)
- [ ] Test admin workflows (user management, link management)

---

## Phase 10: Documentation & Deployment

### 10.1 Documentation
- [ ] Create `README.md` with:
  - Project overview
  - Installation instructions
  - Configuration guide (environment variables)
  - OAuth provider setup guide
  - Development workflow
  - Running the application
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Create configuration template with comments

### 10.2 Deployment Preparation
- [ ] Create Docker setup:
  - Multi-stage `Dockerfile`:
    - Development stage with hot-reload capability via code volume mounts
    - Production stage with optimized image size and dependencies
  - `docker-compose.yaml` for local development (app service only):
    - SQLite database as default for development
    - Volume mounts for code hot-reload
  - `.dockerignore` for efficient builds
- [ ] Document Docker development workflow in README:
  - Quick start: `docker-compose --build up`
  - SQLite database location: `./shortlink.db` (created automatically)
  - How to access application: `http://localhost:5000`
  - How to run commands inside container
- [ ] Create production configuration recommendations:
  - Environment variable requirements
  - Database setup for production (PostgreSQL recommended)
  - Reverse proxy configuration (nginx/caddy)
  - SSL/TLS certificate setup
  - Rate limiting and security headers

---

## UV Configuration & Development Workflow

### `pyproject.toml` Structure
```toml
[project]
name = "shortlink-app"
version = "0.1.0"
description = "Python link shortening service with OAuth2"
requires-python = ">=3.10"
readme = "README.md"
authors = [{name = "Your Name", email = "email@example.com"}]

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[dependency-groups]
dev = [
    "pytest>=7.0",
    "pytest-asyncio",
    "pytest-cov",
    "black",
    "ruff",
    "mypy",
    "pre-commit",
]
migration = [
    "alembic",
]
```

### Development Command Shortcuts
Execute development tasks via UV:
```bash
uv sync                           # Install all dependencies
uv run dev                        # Start development server (local)
docker-compose --build up         # Start development environment (Docker)
uv run test                       # Run test suite with coverage
uv run lint                       # Check code quality (ruff + mypy)
uv run format                     # Auto-format code (black + ruff)
```

### Docker Development Setup
- [ ] **Dockerfile** (single file, multi-stage):
  - Base image: `python:3.10-slim` (or later)
  - Development stage: installs UV, syncs dependencies, mounts code volume for hot-reload
  - Production stage: optimized, minimal dependencies, ready for deployment
  - Supports both `dev` and `prod` targets via build args
- [ ] **docker-compose.yaml**:
  - **app** service:
    - Builds from Dockerfile (development stage)
    - Mounts `./app` and `./tests` as volumes for hot-reload
    - Exposes port 5000
    - Loads environment from `.env`
    - Command: `uv run dev`
    - Default database: SQLite at `./shortlink.db` (local filesystem)

### Pre-commit Configuration (`.pre-commit-config.yaml`)
- [ ] Configure pre-commit to run automatically on commits:
  - Ruff linting (check and auto-fix mode)
  - Black code formatting
  - MyPy type checking (non-blocking, warnings OK)
  - Standard file fixers (trailing whitespace, EOF)
- [ ] Document pre-commit setup in README:
  - How to install hooks: `pre-commit install`
  - How to run hooks manually: `pre-commit run --all-files`

### Development Scripts in `scripts/` Directory

**`scripts/dev.sh`** - Start development server
- [ ] Run Quart development server
- [ ] Enable debug mode and auto-reload
- [ ] Load environment from `.env`
- [ ] Bind to 0.0.0.0:5000 (or configurable)

**`scripts/test.sh`** - Run tests with coverage
- [ ] Execute pytest with asyncio support
- [ ] Generate coverage report
- [ ] Display coverage summary

**`scripts/lint.sh`** - Check code quality
- [ ] Run Ruff linter on `app/`, `tests/`, `run.py`
- [ ] Run MyPy type checker
- [ ] Report findings without auto-fixing

**`scripts/format.sh`** - Auto-format code
- [ ] Run Black formatter
- [ ] Run Ruff in auto-fix mode
- [ ] Report changes made

---

## Key Configuration Variables (`.env` template)

```
# Database
DATABASE_URL=sqlite:///./shortlink.db

# OAuth Providers
OAUTH_PROVIDERS=google,github
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

# JWT/Security
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600
REFRESH_TOKEN_EXPIRATION_DAYS=7

# Application Settings
INSTANCE_NAME=My Short Links
ALLOW_PRIVATE_LINKS_ONLY=false
ENABLE_ALLOW_LIST_MODE=false

# Server
DEBUG=true
HOST=0.0.0.0
PORT=5000
```

---

## Implementation Order Recommendation

1. **Phase 1** - Set up project structure, database, and OAuth authentication
2. **Phase 2** - Implement core link management (CRUD operations)
3. **Phase 3** - Add access control and link redirect logic
4. **Phase 4** - Build admin dashboard and user management
5. **Phase 5** - Implement statistics tracking
6. **Phase 6** - Develop web UI and templates
7. **Phase 7** - Flesh out complete REST API
8. **Phase 8** - Add security measures and error handling
9. **Phase 9** - Write comprehensive test suite
10. **Phase 10** - Documentation and deployment preparation

---

This plan is comprehensive yet flexible. Implementation can proceed phase by phase with clear deliverables for each section.
