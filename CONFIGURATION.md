# Configuration Guide

Complete guide to configuring the Link Shortening Service for development and production environments.

## Environment Variables

### Database Configuration

```bash
# SQLite (Development)
DATABASE_URL=sqlite:///./shortlink.db

# PostgreSQL (Production)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/shortlink_db
```

**Notes:**
- SQLite is suitable for development and small deployments
- PostgreSQL recommended for production
- Connection pooling is automatically configured

### OAuth Providers

#### Google OAuth

```bash
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback/google
```

**Setup Instructions:**
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the "Google+ API"
4. Go to Credentials → Create OAuth 2.0 Client ID (Web application)
5. Add Authorized redirect URI: `http://localhost:5000/auth/callback/google`
6. Copy the Client ID and Client Secret

#### GitHub OAuth

```bash
GITHUB_CLIENT_ID=<your-client-id>
GITHUB_CLIENT_SECRET=<your-client-secret>
GITHUB_REDIRECT_URI=http://localhost:5000/auth/callback/github
```

**Setup Instructions:**
1. Visit [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in application details
4. Set Authorization callback URL: `http://localhost:5000/auth/callback/github`
5. Copy the Client ID and Client Secret

#### Additional OAuth Providers

Currently supports: Google, GitHub

To add more providers, update `app/utils/oauth.py` with the provider configuration.

### JWT & Security

```bash
# JWT Secret Key (for token signing)
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600          # Access token: 1 hour
REFRESH_TOKEN_EXPIRATION_DAYS=7      # Refresh token: 7 days

# CSRF Protection
CSRF_SECRET_KEY=your-csrf-secret-change-in-production
CSRF_TOKEN_EXPIRATION_MINUTES=60     # CSRF token: 1 hour

# Session Security
SESSION_SECURE_COOKIES=false         # Set to true in production with HTTPS
SESSION_HTTPONLY=true                # Recommended: true
```

**Security Best Practices:**
- Use strong, random values for all secret keys (at least 32 characters)
- Never commit `.env` file to version control
- Rotate secrets periodically
- Use different secrets for development and production
- Enable HTTPS in production

### HTTPS & Security Headers

```bash
# HTTPS & Redirects
ENABLE_HTTPS_REDIRECT=false          # Set to true in production
ENABLE_HSTS=true                     # HTTP Strict Transport Security
HSTS_MAX_AGE=31536000                # 1 year in seconds

# Content Security Policy (HSTS)
# Automatically applied by middleware
```

### Application Settings

```bash
# Instance Configuration
INSTANCE_NAME=My Link Shortener
DEBUG=false                          # Set to false in production

# Application Mode
ALLOW_PRIVATE_LINKS_ONLY=false       # If true, only admins can create links
ENABLE_ALLOW_LIST_MODE=false         # If true, registration restricted to allow-list
```

### Server Configuration

```bash
# Server Settings
HOST=0.0.0.0
PORT=5000
WORKERS=4                            # Number of worker processes

# In Docker, use:
# HOST=0.0.0.0 (required for Docker)
# PORT=5000
```

## Configuration by Environment

### Development Environment

**.env**
```bash
# Database
DATABASE_URL=sqlite:///./shortlink.db

# OAuth (local)
GOOGLE_CLIENT_ID=your-dev-client-id
GOOGLE_CLIENT_SECRET=your-dev-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback/google

# JWT
JWT_SECRET_KEY=dev-secret-key
CSRF_SECRET_KEY=dev-csrf-secret

# Security
ENABLE_HTTPS_REDIRECT=false
SESSION_SECURE_COOKIES=false
DEBUG=true

# Application
INSTANCE_NAME=Local Development
```

### Docker Development

The `.env` file is automatically loaded by Docker Compose:

```bash
docker-compose --build up
```

SQLite database is persisted in the local directory.

### Production Environment

**.env.production**
```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@prod-db.example.com:5432/shortlink

# OAuth (production URLs)
GOOGLE_CLIENT_ID=prod-client-id
GOOGLE_CLIENT_SECRET=prod-secret
GOOGLE_REDIRECT_URI=https://links.example.com/auth/callback/google

GITHUB_CLIENT_ID=prod-github-id
GITHUB_CLIENT_SECRET=prod-github-secret
GITHUB_REDIRECT_URI=https://links.example.com/auth/callback/github

# JWT (use strong, random values)
JWT_SECRET_KEY=<generate-strong-random-key>
CSRF_SECRET_KEY=<generate-strong-random-key>

# Security (enable all)
ENABLE_HTTPS_REDIRECT=true
ENABLE_HSTS=true
HSTS_MAX_AGE=31536000
SESSION_SECURE_COOKIES=true

# Application
INSTANCE_NAME=My Organization Links
DEBUG=false
ALLOW_PRIVATE_LINKS_ONLY=false
ENABLE_ALLOW_LIST_MODE=false

# Server
WORKERS=4
```

### Generate Strong Secret Keys

Use Python to generate cryptographically secure keys:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Or use OpenSSL:

```bash
openssl rand -base64 32
```

## Application Features Configuration

### Allow-List Mode

When enabled, only users with emails on the allow-list can register:

```bash
ENABLE_ALLOW_LIST_MODE=true
```

**Managing Allow-List:**
1. Login as admin
2. Go to `/admin/allow-list`
3. Add approved email addresses
4. Users can only register with these emails

### Private Links Only Mode

When enabled, only admins can create links:

```bash
ALLOW_PRIVATE_LINKS_ONLY=true
```

Regular users can only view and access links created by admins.

## Rate Limiting Configuration

Rate limiting is configured in `app/config.py` via the `RateLimiter` service:

### Default Rate Limits

```python
LIMITS = {
    "oauth_login": {"requests": 5, "window_minutes": 15},      # 5 attempts per 15 min
    "link_create": {"requests": 50, "window_minutes": 60},    # 50 links per hour per user
    "link_redirect": {"requests": 1000, "window_minutes": 60}, # 1000 hits per hour per link
}
```

To modify these limits, edit `app/services/rate_limiter.py`.

## Database Pooling Configuration

Connection pooling is automatically configured:

**SQLite (Development):**
```python
engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)
```

**PostgreSQL (Production):**
```python
engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,           # Verify connections before use
    pool_size=20,                 # Number of connections to maintain
    max_overflow=40,              # Additional connections allowed
)
```

## Logging Configuration

Structured logging is implemented via middleware:

**Request Logging:**
- Automatic request ID generation
- Request/response logging with timing
- Admin operation audit trails
- Error logging with context

See `app/middleware/request_logging.py` for details.

## Testing Configuration

Tests use in-memory SQLite database:

```python
test_url = "sqlite+aiosqlite:///:memory:"
```

**Run Tests:**
```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_link_service.py

# With coverage
uv run pytest --cov=app --cov-report=html

# Integration tests only
uv run pytest tests/test_integration_workflows.py -v
```

## Environment Variable Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./shortlink.db` | Database connection string |
| `GOOGLE_CLIENT_ID` | None | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | None | Google OAuth Client Secret |
| `GOOGLE_REDIRECT_URI` | None | Google OAuth redirect URI |
| `GITHUB_CLIENT_ID` | None | GitHub OAuth Client ID |
| `GITHUB_CLIENT_SECRET` | None | GitHub OAuth Client Secret |
| `GITHUB_REDIRECT_URI` | None | GitHub OAuth redirect URI |
| `JWT_SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing key |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXPIRATION_SECONDS` | `3600` | Access token expiration (seconds) |
| `REFRESH_TOKEN_EXPIRATION_DAYS` | `7` | Refresh token expiration (days) |
| `CSRF_SECRET_KEY` | `dev-csrf-secret-change-in-production` | CSRF token signing key |
| `CSRF_TOKEN_EXPIRATION_MINUTES` | `60` | CSRF token expiration (minutes) |
| `ENABLE_HTTPS_REDIRECT` | `false` | Redirect HTTP to HTTPS |
| `ENABLE_HSTS` | `true` | Enable HTTP Strict Transport Security |
| `HSTS_MAX_AGE` | `31536000` | HSTS max age (seconds, 1 year) |
| `SESSION_SECURE_COOKIES` | `false` | Set Secure flag on session cookies |
| `SESSION_HTTPONLY` | `true` | Set HttpOnly flag on session cookies |
| `INSTANCE_NAME` | `My Short Links` | Application instance name |
| `ALLOW_PRIVATE_LINKS_ONLY` | `false` | Only admins can create links |
| `ENABLE_ALLOW_LIST_MODE` | `false` | Restrict registration to allow-list |
| `DEBUG` | `false` | Debug mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `5000` | Server port |

## Troubleshooting Configuration Issues

### Issue: OAuth Login Fails

**Solution:**
1. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
2. Check OAuth redirect URIs match exactly (including protocol and trailing slash)
3. Verify OAuth app is authorized for your domain
4. Check browser console for specific error messages

### Issue: Database Connection Error

**Solution:**
1. Verify `DATABASE_URL` is correct
2. For PostgreSQL, ensure database server is running
3. Check user credentials and database permissions
4. Verify network access to database server

### Issue: CSRF Token Expired

**Solution:**
1. Verify `CSRF_TOKEN_EXPIRATION_MINUTES` is set appropriately
2. Clear browser cookies and try again
3. Check system time is accurate (CSRF tokens are time-dependent)

### Issue: Rate Limiting Too Strict

**Solution:**
Edit `app/services/rate_limiter.py` to adjust `LIMITS`:
```python
LIMITS = {
    "oauth_login": {"requests": 10, "window_minutes": 15},      # More lenient
    "link_create": {"requests": 100, "window_minutes": 60},
    "link_redirect": {"requests": 2000, "window_minutes": 60},
}
```

### Issue: Database Locks (SQLite)

**Solution:**
SQLite has concurrent write limitations. For production with high concurrency, use PostgreSQL:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@db-server:5432/shortlink
```

## Security Checklist

- [ ] All secret keys are strong and random (32+ characters)
- [ ] `DEBUG=false` in production
- [ ] `ENABLE_HTTPS_REDIRECT=true` in production
- [ ] `SESSION_SECURE_COOKIES=true` in production
- [ ] `ENABLE_HSTS=true` in production
- [ ] OAuth redirect URIs use HTTPS in production
- [ ] Database credentials are secure and not in version control
- [ ] `.env` file is in `.gitignore`
- [ ] Regular database backups configured
- [ ] Monitoring and logging are enabled
- [ ] Rate limiting is appropriate for your use case

---

**Last Updated**: February 24, 2026
