# Agent Guidelines for Link Shortening Service

Quick reference for agentic coding in this repository.

## Build & Test Commands

### Running Tests
```bash
# All tests
uv run pytest

# Single test function
uv run pytest tests/test_file.py::TestClass::test_function

# Single test file
uv run pytest tests/test_file.py

# With verbose output
uv run pytest -vv

# Stop on first failure
uv run pytest -x

# Specific test by name pattern
uv run pytest -k "test_create_link"

# With coverage report
uv run pytest --cov=app --cov-report=term-missing
```

### Code Quality
```bash
# Format code (Black + Ruff)
uv run format

# Lint code
uv run lint

# Type checking
uv run mypy app/

# All checks
uv run lint && uv run format && uv run mypy app/

# Pre-commit hooks (runs on all files)
pre-commit run --all-files
```

### Development
```bash
# Run local dev server
uv run dev

# Run with Docker
docker-compose --build up
```

---

## Code Style Guidelines

### Imports
- Group imports: stdlib → third-party → local
- Sort alphabetically within groups
- One import per line for clarity
- Use absolute imports (not relative)

```python
import asyncio
from typing import Optional

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.services.link_service import LinkService
```

### Formatting
- **Line length**: 100 characters (Black/Ruff enforced)
- **Indentation**: 4 spaces
- **Type hints**: Required for all functions
- **Docstrings**: Google-style for all public functions

```python
async def create_link(
    db_session: AsyncSession,
    user_id: int,
    original_url: str,
    is_public: bool = True,
) -> Link:
    """Create a shortened link.
    
    Args:
        db_session: Database session
        user_id: User creating the link
        original_url: URL to shorten
        is_public: Whether link is public
        
    Returns:
        Created Link object
        
    Raises:
        ValidationError: If validation fails
        ConflictError: If slug already exists
    """
```

### Type Hints
- Use `Optional[T]` for nullable types (not `T | None`)
- Import types from `typing` module
- Annotate async functions with proper return types

```python
from typing import Optional, List

async def get_user(user_id: int) -> Optional[User]:
    """..."""
```

### Naming Conventions
- **Functions**: `lowercase_with_underscores`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_CASE`
- **Private**: Leading underscore `_private_method`
- **Async functions**: Same as sync, prefix `async def`
- **Database models**: Singular noun `User` not `Users`

### Error Handling
- Raise custom exceptions, don't use `Exception`
- Available exceptions in `app/exceptions.py`:
  - `ValidationError` - Invalid input
  - `ConflictError` - Resource conflict (duplicate slug)
  - `NotFoundError` - Resource not found
  - `ForbiddenError` - Access denied
  - `UnauthorizedError` - Authentication required

```python
if not url_is_valid(url):
    raise ValidationError(f"Invalid URL: {url}")

if duplicate_slug:
    raise ConflictError(f"Slug '{slug}' already exists")

if not resource:
    raise NotFoundError(f"Link {link_id} not found")

if user_id != link.user_id:
    raise ForbiddenError("You don't own this link")
```

### Async/Await
- All database operations are async
- Use `await` for async calls, never block
- Use `async def` for route handlers and service methods
- Test with `pytest-asyncio` (auto-enabled)

```python
async def get_link(db_session: AsyncSession, link_id: int) -> Link:
    stmt = select(Link).where(Link.id == link_id)
    result = await db_session.execute(stmt)
    link = result.scalar_one_or_none()
    if not link:
        raise NotFoundError(...)
    return link
```

---

## Project Structure

**Core files**:
- `app/models/` - SQLAlchemy ORM models
- `app/services/` - Business logic (LinkService, UserService, etc.)
- `app/routes/` - API endpoints and web routes
- `app/middleware/` - CSRF, security headers, error handling
- `app/exceptions.py` - Custom exception classes
- `tests/` - 344+ tests (see conftest.py for fixtures)

**Important**: Services handle business logic, routes are thin wrappers. Database operations go in services.

---

## Testing Patterns

Use pytest fixtures from `conftest.py`:
- `db_session` - Fresh async database per test
- `test_user` - Pre-created user
- `test_link` - Pre-created link

```python
async def test_user_can_create_link(
    db_session: AsyncSession,
    test_user: User,
):
    """Test link creation."""
    service = LinkService(db_session)
    link = await service.create_link(
        user_id=test_user.id,
        original_url="https://example.com",
    )
    assert link.user_id == test_user.id
```

---

## Pre-commit Hooks

Automatically runs on commit. Tools:
- **Ruff** - Linting (E, F, W, I codes)
- **Black** - Formatting
- **MyPy** - Type checking
- **Trailing whitespace/EOF fixer**

To bypass (not recommended):
```bash
git commit --no-verify
```

---

## Security Features (Maintain)

When making changes, preserve:
- **CSRF tokens** (middleware/csrf.py) - all forms use tokens
- **Security headers** (middleware/security_headers.py)
- **Input validation** (utils/validators.py) - validate URLs, emails, slugs
- **Error handling** (middleware/error_handler.py) - catch and log all errors
- **Rate limiting** (services/rate_limiter.py) - for sensitive endpoints

---

## Performance Considerations

- Avoid N+1 queries - use eager loading/joins
- Cache frequently accessed data
- Use indexes for common filters
- Test performance with benchmarks if adding heavy operations

---

## Documentation

- Update README.md if adding user-facing features
- Update CONFIGURATION.md for new env vars
- Update CONTRIBUTING.md if workflow changes
- Add docstrings to all public functions
