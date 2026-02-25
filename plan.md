# Python Link Shortening Application - Implementation Plan

## Completion Status

### ✅ Phase 1: Core Infrastructure & Data Models
- ✅ Project setup with UV package manager
- ✅ Configuration management (`config.py`)
- ✅ SQLAlchemy ORM models (User, Link, OAuthAccount, AllowListEntry)
- ✅ Utilities: Slug generator, validators
- ✅ Custom exception hierarchy
- ✅ Alembic database migration setup
- ✅ Docker multi-stage build and docker-compose configuration
- ✅ Pre-commit hooks (ruff, black, mypy)
- ✅ Development scripts (dev.sh, test.sh, lint.sh, format.sh)

### ✅ Phase 2: Unit Tests & Service Layer
- ✅ Test infrastructure (pytest fixtures with fresh in-memory SQLite per test)
- ✅ Utilities tests (27 tests):
  - Slug generation tests (13 tests)
  - Validator tests (14 tests)
- ✅ ORM Model tests (54 tests):
  - Link model tests (14 tests)
  - User model tests (19 tests)
  - OAuth account tests (18 tests)
  - Access control tests (16 tests)
- ✅ Service layer implementation & tests (16 tests):
  - LinkService (create, read, update, delete, access control, slug validation)
  - UserService (CRUD, admin operations, blocking)
  - AuthService (OAuth linking, provider lookups, token management)
- **Total: 110 tests passing** ✅

### 🔄 Phase 3: Database Integration Setup (IN PROGRESS)
- [ ] Connection pooling configuration
- [ ] Async context management
- [ ] Dependency injection setup

### ⏳ Phase 4: Authentication Implementation
- [ ] JWT token generation/validation
- [ ] OAuth2 flows for configured providers
- [ ] Token refresh and revocation

### ⏳ Phase 5-13: Feature Implementation
- [ ] API endpoints, admin dashboard, web UI, security, integration tests, deployment

---

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

## Phase 1: Core Infrastructure & Data Models (✅ COMPLETED)

### 1.1 Project Setup (✅ COMPLETED)
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

### 1.2 Database Layer (✅ COMPLETED)
- [ ] Create SQLAlchemy models:
  - **User**: id, email, full_name, avatar_url, is_admin, is_blocked, created_at, updated_at
  - **Link**: id, user_id, original_url, slug, is_public, allowed_emails, created_at, updated_at, hit_count, last_hit_at
  - **OAuthAccount**: id, user_id, provider, provider_user_id, provider_email, access_token, refresh_token, created_at
  - **AllowListEntry**: id, email, created_at (for allow-list mode management)
- [ ] Set up Alembic for database migrations
- [ ] Create initial migration script
- [ ] Implement database initialization (with first user setup as admin)
- [ ] Add database utilities for common operations

### 1.3 OAuth2 Authentication (⏳ Phase 4)
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

## Phase 2: Unit Tests & Service Layer (✅ COMPLETED)

### 2.1 Test Infrastructure (✅ COMPLETED)
- ✅ Pytest setup with asyncio support
- ✅ Fixtures for fresh in-memory SQLite database per test (prevents UNIQUE constraint conflicts)
- ✅ Test user, link, and admin fixtures
- ✅ Test database initialization

### 2.2 Utilities Tests (✅ COMPLETED - 27 tests)
- ✅ Slug generation tests (13 tests):
  - Random slug generation with default/custom lengths
  - Base62 character validation
  - Randomness and uniqueness verification
  - Length validation and error handling
- ✅ Validator tests (14 tests):
  - URL validation (protocol, domain, max length)
  - Email validation and normalization
  - Full name validation
  - Edge cases and error handling

### 2.3 ORM Model Tests (✅ COMPLETED - 54 tests)
- ✅ Link model tests (14 tests):
  - Model creation and persistence
  - Relationships (owner, allowed emails)
  - Timestamps and auto-generation
  - Hit count tracking
- ✅ User model tests (19 tests):
  - User creation and CRUD operations
  - Cascade deletion (links deleted when user deleted)
  - Admin and blocked status management
  - Email normalization on save
- ✅ OAuth account tests (18 tests):
  - OAuth account creation and linking
  - Provider credential storage
  - Multiple OAuth accounts per user
  - User creation from OAuth providers
- ✅ Access control tests (16 tests):
  - Public link access
  - Private link access restrictions
  - Email allowlist enforcement
  - Admin and blocked user status effects

### 2.4 Service Layer Implementation (✅ COMPLETED - 16 tests)
- ✅ LinkService:
  - Create links with random/custom slugs
  - Slug uniqueness and validation (Base62 only)
  - Original URL validation
  - Access control checking (public/private/allowlist)
  - Update and delete with ownership verification
  - Hit count incrementing
  - CRUD queries
- ✅ UserService:
  - User creation and profile updates
  - Admin promotion/demotion
  - User blocking/unblocking
  - Cascade deletion
  - User queries (by email, admin list, blocked list, with links)
- ✅ AuthService:
  - OAuth account creation and linking
  - User creation from OAuth providers
  - Provider credential lookups and updates
  - Account unlinking

---

## Phase 3: Database Integration Setup (⏳ IN PROGRESS)

### 3.1 Connection Pooling
- [ ] Implement async connection pool for PostgreSQL support
- [ ] Configure pool size, overflow, and timeout settings
- [ ] Add health check mechanism for stale connections

### 3.2 Async Context Management
- [ ] Create database session factory
- [ ] Implement async context manager for database transactions
- [ ] Set up request-scoped session management for Quart

### 3.3 Dependency Injection
- [ ] Create dependency injection container for services
- [ ] Wire services with database sessions
- [ ] Set up factory pattern for service creation

---

## Phase 4: Authentication Implementation

### 4.1 JWT Token Management
- [ ] Implement JWT token generation with user claims
- [ ] Implement JWT token validation middleware
- [ ] Add token refresh token mechanism
- [ ] Implement token revocation/blacklisting

### 4.2 OAuth2 Provider Integration
- [ ] Create OAuth2 provider abstraction layer
- [ ] Implement Google OAuth2 flow
- [ ] Implement GitHub OAuth2 flow
- [ ] Add configurable provider support
- [ ] Implement OAuth callback handling

### 4.3 Authentication Routes
- [ ] `GET /auth/login/<provider>` - Start OAuth flow
- [ ] `GET /auth/callback/<provider>` - OAuth callback
- [ ] `POST /auth/logout` - Logout and revoke tokens
- [ ] `GET /auth/me` - Get current user info
- [ ] `POST /auth/refresh` - Refresh JWT token

---

## Phase 5: Link Management API Endpoints

### 5.1 Link Creation & Management
- [ ] `POST /api/links` - Create new link (requires auth)
- [ ] `GET /api/links` - List user's links (requires auth, paginated)
- [ ] `GET /api/links/<id>` - Get link details (requires auth + ownership)
- [ ] `PATCH /api/links/<id>` - Update link (requires auth + ownership)
- [ ] `DELETE /api/links/<id>` - Delete link (requires auth + ownership)

### 5.2 Link Request/Response Validation
- [ ] Create Pydantic schemas for link requests and responses
- [ ] Implement request validation middleware
- [ ] Implement consistent error response formatting

---

## Phase 6: Link Redirect Logic & Access Control

### 6.1 Link Redirect Endpoint
- [ ] `GET /<slug>` - Redirect to original URL
- [ ] Implement public link redirect (anyone can access)
- [ ] Implement private link access control:
  - Unauthenticated users → 401 with login option
  - Authenticated but unauthorized → 403
  - Email allowlist checking
- [ ] Implement hit count tracking on redirect
- [ ] Return proper redirect responses (301/302)

### 6.2 Access Control Middleware
- [ ] Create permission checking decorator
- [ ] Implement ownership verification
- [ ] Implement admin-only access checks

---

## Phase 7: User Management API Endpoints

### 7.1 User Management Routes (Admin Only)
- [ ] `GET /api/users` - List all users (paginated)
- [ ] `GET /api/users/<id>` - Get user details
- [ ] `PATCH /api/users/<id>/admin` - Toggle admin status
- [ ] `PATCH /api/users/<id>/block` - Toggle blocked status
- [ ] `DELETE /api/users/<id>` - Delete user

### 7.2 Admin Allow-List Management API
- [ ] `GET /api/admin/allow-list` - List allowed emails
- [ ] `POST /api/admin/allow-list` - Add email to allow-list
- [ ] `DELETE /api/admin/allow-list/<email>` - Remove email from allow-list

---

## Phase 8: Admin Dashboard Backend & User Dashboard Backend

### 8.1 Admin Dashboard API Endpoints
- [ ] `GET /api/admin/dashboard` - Dashboard statistics and overview
- [ ] `GET /api/admin/config` - Instance configuration display
- [ ] System statistics (total links, users, hits)
- [ ] Recent activity tracking

### 8.2 User Dashboard API Endpoints
- [ ] User profile information
- [ ] User's link list with statistics
- [ ] Statistics aggregation (total hits, recent activity)

---

## Phase 9: Web UI & Templates

### 9.1 Base Layout & Navigation
- [ ] Create `base.html` with navigation, responsive design
- [ ] Implement consistent styling (CSS framework or custom)

### 9.2 Authentication Pages
- [ ] Create `login.html` with dynamic OAuth provider buttons
- [ ] Create logout functionality

### 9.3 User Dashboard UI
- [ ] Create `dashboard.html` with user's links table
- [ ] Link creation form/modal
- [ ] Link statistics display
- [ ] Link edit/delete UI
- [ ] Copy-to-clipboard for slugs

### 9.4 Link Detail Page
- [ ] Create `link_detail.html`
- [ ] Display original URL and slug
- [ ] QR code generation for shortened URL
- [ ] Access statistics display
- [ ] Edit form

### 9.5 Admin Dashboard UI
- [ ] Admin dashboard page (`admin/dashboard.html`)
- [ ] Admin links management page (`admin/links.html`)
- [ ] Admin users management page (`admin/users.html`)
- [ ] Allow-list management UI

### 9.6 Error Pages
- [ ] `401.html` (Unauthenticated)
- [ ] `403.html` (Forbidden)
- [ ] `404.html` (Not found)
- [ ] `500.html` (Server error)

---

## Phase 10: Advanced Features

### 10.1 Statistics & Analytics
- [ ] Implement per-link hit count tracking
- [ ] Implement per-user aggregated statistics
- [ ] Implement system-wide statistics
- [ ] (Optional: hourly/daily breakdown, geographic data, referrer tracking)

### 10.2 Rate Limiting
- [ ] Implement rate limiting on OAuth login attempts
- [ ] Implement rate limiting on link creation (per user)
- [ ] Implement rate limiting on link redirects (per link)

### 10.3 Custom Domain Support (Future)
- [ ] Allow admins to configure custom domains
- [ ] Route custom domain requests to shortened links

---

## Phase 11: Security Hardening & Error Handling

### 11.1 Security Measures
- [ ] Implement CSRF protection for web forms
- [ ] Implement security headers (HSTS, CSP, X-Frame-Options)
- [ ] Implement input sanitization
- [ ] Secure token storage best practices

### 11.2 Global Error Handling
- [ ] Create global error handler middleware
- [ ] Implement consistent error response formatting
- [ ] Implement proper HTTP status codes
- [ ] Add structured error logging

---

## Phase 12: Integration Tests & End-to-End Tests

### 12.1 Integration Tests
- [ ] Test OAuth flow with mocked OAuth provider
- [ ] Test link creation and redirect flow
- [ ] Test private link access control
- [ ] Test admin operations

### 12.2 End-to-End Tests
- [ ] Test complete user workflows (signup → create link → redirect)
- [ ] Test admin workflows (user management, link management, allow-list management)

---

## Phase 13: Documentation & Deployment Preparation

### 13.1 Documentation
- [ ] Update `README.md` with:
  - Project overview
  - Installation instructions
  - Configuration guide
  - OAuth provider setup
  - Development workflow
  - Running the application
- [ ] Create API documentation (OpenAPI/Swagger)

### 13.2 Deployment Setup
- [ ] Docker Compose for production
- [ ] PostgreSQL database setup guide
- [ ] Environment variable reference
- [ ] Deployment checklist



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

1. **Phase 1** - Set up project structure, database models, utilities, and custom exceptions
2. **Phase 2** - Unit tests: Data models, validators, slug generation, service logic (TDD)
3. **Phase 3** - Database integration setup (connection pooling, migrations, async context)
4. **Phase 4** - Authentication (JWT token generation/validation, OAuth2 flows)
5. **Phase 5** - Link Management API endpoints (CRUD operations)
6. **Phase 6** - Link Redirect Logic & Access Control
7. **Phase 7** - User Management API endpoints (admin operations)
8. **Phase 8** - Admin Dashboard Backend & User-Facing Dashboard Backend
9. **Phase 9** - Web UI & Templates (HTML/CSS/JavaScript)
10. **Phase 10** - Advanced Features (rate limiting, analytics, custom domains)
11. **Phase 11** - Security Hardening & Error Handling
12. **Phase 12** - Integration Tests & End-to-End Tests
13. **Phase 13** - Documentation & Deployment Preparation

---

This plan is comprehensive yet flexible. Implementation can proceed phase by phase with clear deliverables for each section.
