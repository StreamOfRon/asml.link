# Link Shortening Service

A modern Python-based link shortening service built with **Quart** (async web framework), featuring OAuth2 authentication, flexible access control, rate limiting, and comprehensive admin capabilities.

**Status**: Phase 12 Complete (344 passing tests) | Production Ready

## Features

### Core Features
- 🔗 **URL Shortening** - Create and manage shortened links with custom or auto-generated slugs
- 🔐 **OAuth2 Authentication** - Login with Google, GitHub, and other OAuth providers
- 🛡️ **Access Control** - Public, private, and email-restricted links
- 📊 **Analytics & Rate Limiting** - Track link hits and enforce rate limits on API endpoints
- 👥 **User Management** - Admin controls for users, blocking, and promotion
- ✅ **Allow-List Mode** - Restrict registration to approved email domains
- 🎯 **Admin Dashboard** - Manage users, links, and system configuration

### Security Features
- **CSRF Protection** - Token-based CSRF protection for web forms
- **Security Headers** - HSTS, CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy
- **Rate Limiting** - Per-IP and per-user rate limiting on sensitive endpoints
- **JWT Tokens** - Secure, stateless authentication with refresh tokens
- **Input Validation** - Comprehensive URL, email, and slug validation
- **Structured Logging** - Request IDs and audit trails for security analysis

### Advanced Features
- **Hit Tracking** - Automatic hit count increments with timestamps
- **Email Allowlist** - Per-link email restrictions for private sharing
- **Admin Audit Trails** - Structured logging of admin operations
- **Async Processing** - Full async/await support for high concurrency
- **Database Migrations** - Alembic for schema management

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | Quart (async web framework) |
| **Database** | SQLAlchemy 2.0+ (async ORM) with SQLite/PostgreSQL |
| **Authentication** | OAuth2, JWT, Authlib |
| **Validation** | Pydantic |
| **Testing** | Pytest (344+ tests) |
| **Package Manager** | UV |
| **Python Version** | 3.11+ required |
| **Containerization** | Docker & Docker Compose |

## Quick Start

### Prerequisites
- Python 3.11 or higher
- UV package manager
- Git

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/link-shortening-service.git
cd link-shortening-service
```

2. **Install dependencies**
```bash
uv sync
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your OAuth provider credentials
```

4. **Run development server**
```bash
uv run dev
```

The application will start at `http://localhost:5000`

### Docker Development

```bash
docker-compose --build up
```

Application automatically reloads on code changes. SQLite database is persisted locally.

## Configuration

### Environment Variables

See `CONFIGURATION.md` for detailed configuration options.

**Essential Variables:**
```bash
# Database
DATABASE_URL=sqlite:///./asml-link.db

# OAuth Providers (Google)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback/google

# OAuth Providers (GitHub)
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_REDIRECT_URI=http://localhost:5000/auth/callback/github

# JWT Security
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600

# CSRF Protection
CSRF_SECRET_KEY=your-csrf-secret-change-in-production
CSRF_TOKEN_EXPIRATION_MINUTES=60

# Application
INSTANCE_NAME=My Link Shortener
ALLOW_PRIVATE_LINKS_ONLY=false
ENABLE_ALLOW_LIST_MODE=false
```

### OAuth Provider Setup

#### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `http://localhost:5000/auth/callback/google`
6. Copy Client ID and Client Secret to `.env`

#### GitHub OAuth
1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:5000/auth/callback/github`
4. Copy Client ID and Client Secret to `.env`

## API Documentation

### Web UI Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home (redirects to /login if not authenticated) |
| `/login` | GET | Login page with OAuth provider options |
| `/auth/login/<provider>` | GET | Start OAuth flow |
| `/auth/callback/<provider>` | GET | OAuth callback handler |
| `/logout` | GET | Logout |
| `/dashboard` | GET | User dashboard (requires auth) |
| `/admin` | GET | Admin dashboard (requires admin) |
| `/admin/users` | GET | User management page (requires admin) |
| `/admin/allow-list` | GET | Allow-list management page (requires admin) |

### REST API Endpoints

**Link Management:**
- `POST /api/links` - Create new link
- `GET /api/links` - List user's links (paginated)
- `GET /api/links/<id>` - Get link details
- `PATCH /api/links/<id>` - Update link
- `DELETE /api/links/<id>` - Delete link

**User Management (Admin Only):**
- `GET /api/users` - List all users
- `GET /api/users/<id>` - Get user details
- `PATCH /api/users/<id>/admin` - Toggle admin status
- `PATCH /api/users/<id>/block` - Toggle blocked status
- `DELETE /api/users/<id>` - Delete user

**Allow-List Management (Admin Only):**
- `GET /api/admin/allow-list` - List allowed emails
- `POST /api/admin/allow-list` - Add email to allow-list
- `DELETE /api/admin/allow-list/<email>` - Remove email

**Statistics:**
- `GET /api/stats` - System statistics
- `GET /api/links/<id>/stats` - Link statistics

**Link Redirect:**
- `GET /<slug>` - Redirect to original URL (tracks hit)

### OpenAPI/Swagger Documentation

When running locally, access Swagger UI at:
```
http://localhost:5000/docs
```

ReDoc documentation available at:
```
http://localhost:5000/redoc
```

## Development Workflow

### Running Tests

```bash
# Run all tests
./scripts/test.sh

# Run lint checks
./scripts/lint.sh
```

**Test Coverage:**
- 344+ tests total
- Unit tests for utilities, models, and services
- Integration tests for workflows
- End-to-end tests for user and admin workflows
- All tests passing ✅

### Code Quality

```bash
# Run lint checks
./scripts/lint.sh

# Run tests
./scripts/test.sh
```

### CI / GitHub Actions

- PR checks run via `.github/workflows/pr-checks.yml` and use the `astral-sh/setup-uv@v1` action to install `uv` and the requested Python version. The action also provides caching for `uv` artifacts so CI runs faster.
- Dependabot config is in `.github/dependabot.yml` and will open weekly updates for Python, GitHub Actions, and Docker.
- To reproduce the CI steps locally: run
```bash
uv sync
uv run pytest
uv run lint
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Project Structure

```
link-shortening-service/
├── app/
│   ├── __init__.py              # App factory
│   ├── config.py                # Configuration management
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── link.py
│   │   ├── oauth_account.py
│   │   ├── allow_list_entry.py
│   │   └── rate_limit_entry.py
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── routes/                  # Route handlers
│   │   ├── auth.py              # OAuth/JWT routes
│   │   ├── links.py             # Link CRUD API
│   │   ├── redirect.py          # URL redirect
│   │   ├── users.py             # User management API
│   │   ├── admin.py             # Admin API
│   │   └── web.py               # Web UI routes
│   ├── services/                # Business logic
│   │   ├── link_service.py
│   │   ├── user_service.py
│   │   ├── auth_service.py
│   │   ├── rate_limiter.py
│   │   └── stats_service.py
│   ├── middleware/              # Middleware
│   │   ├── auth.py              # JWT verification
│   │   ├── csrf.py              # CSRF protection
│   │   ├── security_headers.py  # Security headers
│   │   ├── error_handler.py     # Error handling
│   │   └── request_logging.py   # Request logging
│   ├── utils/                   # Utilities
│   │   ├── validators.py        # Input validation
│   │   ├── slug_generator.py    # Slug generation
│   │   └── oauth.py             # OAuth utilities
│   ├── templates/               # Jinja2 templates
│   └── static/                  # CSS, JS, images
├── tests/                       # Test suite (344+ tests)
├── migrations/                  # Alembic migrations
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yaml          # Development environment
├── pyproject.toml              # Project configuration
├── README.md                   # This file
├── CONFIGURATION.md            # Configuration guide
├── DEPLOYMENT.md               # Production deployment
└── CONTRIBUTING.md             # Contributor guidelines
```

## Deployment

### Production Deployment

See `DEPLOYMENT.md` for complete production deployment guide including:
- Docker production image
- PostgreSQL database setup
- Environment configuration for production
- Nginx reverse proxy configuration
- SSL/TLS certificate setup
- Health checks and monitoring

### Quick Production Checklist

- [ ] Set strong `JWT_SECRET_KEY` and `CSRF_SECRET_KEY`
- [ ] Configure `DATABASE_URL` for PostgreSQL
- [ ] Set `ENABLE_HTTPS_REDIRECT=true`
- [ ] Enable HSTS with `HSTS_MAX_AGE=31536000`
- [ ] Set secure OAuth redirect URIs
- [ ] Configure allow-list mode if needed
- [ ] Set up database backups
- [ ] Enable request logging and monitoring
- [ ] Test all OAuth provider integrations
- [ ] Verify rate limiting is working

## Contributing

See `CONTRIBUTING.md` for:
- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

## Performance & Scalability

### Features
- **Async/Await** - Full async support for high concurrency
- **Connection Pooling** - Configured for SQLAlchemy
- **Caching** - HTTP caching headers for shortened links
- **Rate Limiting** - Built-in rate limiting on sensitive endpoints
- **Pagination** - All list endpoints support pagination

### Benchmarks
- **Test Suite**: 344 tests complete in ~2.4 seconds
- **Database**: Supports SQLite (development) and PostgreSQL (production)
- **Hit Tracking**: Efficient counter increments with minimal database overhead

## Monitoring & Logging

### Structured Logging
- Request IDs for tracing
- Admin operation audit trails
- Error logging with context
- Access logs with response times

### Metrics
- Link hit counts per link
- User statistics
- System-wide statistics
- Rate limit tracking

## Security

### Best Practices
- ✅ CSRF protection on all forms
- ✅ Security headers (HSTS, CSP, X-Frame-Options)
- ✅ JWT tokens with expiration
- ✅ Password hashing (if enabled)
- ✅ Input validation and sanitization
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ XSS protection (Jinja2 auto-escaping)
- ✅ Rate limiting on sensitive endpoints
- ✅ Admin operation logging
- ✅ Allow-list mode for restricted access

## License

MIT License - see LICENSE file for details

## Support & Documentation

- **API Docs**: `/docs` (Swagger UI) or `/redoc` (ReDoc)
- **Configuration**: See `CONFIGURATION.md`
- **Deployment**: See `DEPLOYMENT.md`
- **Contributing**: See `CONTRIBUTING.md`
- **Issues**: Please report bugs on GitHub

## Roadmap

- [ ] Custom domain support
- [ ] QR code generation for links
- [ ] Analytics dashboard with charts
- [ ] Webhook notifications
- [ ] Link expiration dates
- [ ] Bulk link import/export
- [ ] Advanced search and filtering
- [ ] API key management for programmatic access

## Development Status

| Phase | Status | Tests | Description |
|-------|--------|-------|-------------|
| Phase 1 | ✅ Complete | 0 | Core Infrastructure & Data Models |
| Phase 2 | ✅ Complete | 110 | Unit Tests & Service Layer |
| Phase 3 | ✅ Complete | N/A | Database Integration Setup |
| Phase 4 | ✅ Complete | 63 | Authentication Implementation |
| Phase 5 | ✅ Complete | 55 | Link Management API Endpoints |
| Phase 6 | ✅ Complete | 60 | Link Redirect Logic & Access Control |
| Phase 7 | ✅ Complete | 78 | User Management API Endpoints |
| Phase 8 | ✅ Complete | 178 | Admin & User Dashboard APIs |
| Phase 9 | ✅ Complete | 69 | Web UI & Templates |
| Phase 10 | ✅ Complete | 133 | Advanced Features (Analytics, Rate Limiting) |
| Phase 11 | ✅ Complete | 34 | Security Hardening & Error Handling |
| Phase 12 | ✅ Complete | 24 | Integration & End-to-End Tests |
| Phase 13 | 🟡 In Progress | N/A | Documentation & Deployment |

## Credits

Built with ❤️ using Quart, SQLAlchemy, and OAuth2.

---

**Last Updated**: February 24, 2026
**Python Version**: 3.11+ required
**Total Test Coverage**: 344 tests, all passing
