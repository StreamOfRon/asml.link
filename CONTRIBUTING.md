# Contributing Guide

Thank you for contributing to the Link Shortening Service! This guide will help you set up the development environment and contribute effectively.

## Code of Conduct

- Be respectful and inclusive
- Ask for help when needed
- Provide constructive feedback
- Focus on the code, not the person

## Getting Started

### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/yourusername/link-shortening-service.git
cd link-shortening-service
```

### 2. Set Up Development Environment

```bash
# Install dependencies
uv sync

# Create .env file
cp .env.example .env

# Install pre-commit hooks
pre-commit install

# Verify setup
uv run pytest
```

### 3. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Running the Application

```bash
# Local development
uv run dev

# With Docker
docker-compose --build up

# Application available at http://localhost:5000
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_link_service.py

# With coverage report
uv run pytest --cov=app --cov-report=html

# Integration tests only
uv run pytest tests/test_integration_workflows.py -v

# Verbose output
uv run pytest -vv

# Stop on first failure
uv run pytest -x
```

### Code Quality

```bash
# Format code
uv run format

# Run linting
uv run lint

# Type checking
uv run mypy app/

# All checks
uv run lint && uv run format && uv run mypy app/
```

### Pre-commit Hooks

Hooks run automatically on commit:

```bash
# Ruff linting and formatting
# Black code formatting
# MyPy type checking
# Trailing whitespace/EOF fixer
```

To run hooks manually:

```bash
pre-commit run --all-files
```

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 100 characters
- Use descriptive variable names

**Example:**

```python
async def create_link(
    user_id: int,
    original_url: str,
    slug: Optional[str] = None,
    is_public: bool = True,
) -> Link:
    """Create a new shortened link.

    Args:
        user_id: ID of the user creating the link
        original_url: Original URL to shorten
        slug: Custom slug (optional, generates if not provided)
        is_public: Whether link is publicly accessible

    Returns:
        Created Link object

    Raises:
        ValidationError: If validation fails
    """
    # Implementation
    pass
```

### Documentation

- Write docstrings for all public functions
- Use Google-style docstrings
- Add examples for complex functions
- Keep README updated

### Testing

- Write tests for new features
- Test both happy path and error cases
- Use descriptive test names
- Aim for 90%+ coverage

**Example Test:**

```python
async def test_user_can_create_link(self, db_session: AsyncSession, test_user: User):
    """Test user can create a new link."""
    service = LinkService(db_session)

    link = await service.create_link(
        user_id=test_user.id,
        original_url="https://example.com",
        slug="test",
        is_public=True,
    )

    assert link.slug == "test"
    assert link.user_id == test_user.id
    assert link.is_public is True
```

## Project Structure

```
app/
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── routes/              # Route handlers
├── services/            # Business logic
├── middleware/          # Custom middleware
├── utils/               # Utilities and helpers
├── templates/           # Jinja2 templates
└── static/              # CSS, JS, images

tests/
├── conftest.py         # Pytest fixtures
├── test_*.py           # Test files
└── test_integration_workflows.py  # Integration/E2E tests
```

## Making Changes

### 1. Create Feature Branch

```bash
git checkout -b feature/add-qr-codes
```

### 2. Make Changes

- Keep commits focused and descriptive
- One feature per branch
- Test frequently

### 3. Write Tests

For every feature, write:
- Unit tests (test individual functions)
- Integration tests (test workflows)

```bash
# Ensure all tests pass
uv run pytest

# Check coverage
uv run pytest --cov=app --cov-report=term-missing
```

### 4. Code Review

```bash
# Format code
uv run format

# Run linting
uv run lint

# Type checking
uv run mypy app/
```

### 5. Commit Changes

```bash
# Add files
git add .

# Commit with descriptive message
git commit -m "feat: Add QR code generation for links

- Generate QR codes using qrcode library
- Display on link detail page
- Support for different QR sizes"
```

### Commit Message Format

Follow conventional commits:

```
type(scope): subject

body

footer
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `test:` - Tests only
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `perf:` - Performance improvement
- `style:` - Formatting changes
- `chore:` - Dependency updates, etc.

**Examples:**

```
feat(links): Add QR code generation for shortened links
fix(auth): Handle expired refresh tokens correctly
test(rate-limiter): Add integration tests for rate limiting
docs: Update README with deployment guide
refactor(services): Extract common validation logic
```

### 6. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/add-qr-codes

# Create PR on GitHub
# Fill in PR template with:
# - Description of changes
# - Related issues
# - Testing notes
```

## Pull Request Process

1. **Description**: Clearly describe what and why
2. **Tests**: Include tests for new features
3. **Documentation**: Update docs if needed
4. **Code Review**: Address reviewer feedback
5. **CI/CD**: All checks must pass

### PR Checklist

- [ ] Tests pass: `uv run pytest`
- [ ] Coverage maintained or improved
- [ ] Code formatted: `uv run format`
- [ ] Linting passes: `uv run lint`
- [ ] Type checking passes: `uv run mypy app/`
- [ ] Documentation updated
- [ ] No breaking changes to API
- [ ] Commit messages follow conventions

## Testing Guidelines

### Unit Tests

Test individual functions in isolation:

```python
async def test_validate_url_accepts_valid_urls(self):
    """Test that valid URLs are accepted."""
    valid_urls = [
        "https://example.com",
        "http://example.com/path?query=1",
        "https://sub.example.com:8080",
    ]

    for url in valid_urls:
        assert is_valid_url(url) is True
```

### Integration Tests

Test features working together:

```python
async def test_user_creates_link_and_redirects(
    self, db_session: AsyncSession, test_user: User
):
    """Test complete workflow: create link → retrieve → redirect."""
    # Create link
    link = await service.create_link(...)

    # Retrieve link
    retrieved = await service.get_link_by_slug(link.slug)
    assert retrieved is not None

    # Track hit
    updated = await service.increment_hit_count(link.slug)
    assert updated.hit_count == 1
```

### Test Fixtures

Use existing fixtures from `conftest.py`:

```python
async def test_something(
    self,
    db_session: AsyncSession,      # Database session
    test_user: User,               # Regular user
    test_admin_user: User,         # Admin user
    test_link: Link,               # Public link
    test_private_link: Link,       # Private link
):
    """Test using fixtures."""
    pass
```

## Database Migrations

When modifying models:

```bash
# Generate migration
alembic revision --autogenerate -m "Add new column to links"

# Review migration file
cat migrations/versions/xxxxx_add_new_column.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Performance Considerations

- Use database indexes for frequently queried columns
- Implement caching for expensive operations
- Consider async performance implications
- Profile before optimizing

## Security Considerations

- Validate all user input
- Use parameterized queries (SQLAlchemy handles this)
- Escape output in templates
- Check authentication/authorization
- Rate limit sensitive endpoints
- Hash sensitive data appropriately

## Documentation

### Update README.md for:
- New features
- API changes
- Configuration options

### Update docstrings for:
- New functions
- Changed signatures
- New parameters

### Update CONFIGURATION.md for:
- New environment variables
- New configuration options

## Reporting Issues

When reporting bugs, include:

```markdown
## Description
Brief description of the issue

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Steps to Reproduce
1. Step 1
2. Step 2
3. ...

## Environment
- Python version
- OS
- Relevant error messages

## Screenshots
If applicable
```

## Feature Requests

Include:

```markdown
## Description
What feature do you want?

## Use Case
Why do you need this?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches?
```

## Questions or Need Help?

- Check existing issues
- Read documentation
- Ask in discussions/issues
- Open a GitHub discussion

## Review Process

1. **Automated Checks**
   - All tests must pass
   - Code coverage maintained
   - Linting must pass

2. **Code Review**
   - At least 1 reviewer
   - Feedback addressed
   - Approved by maintainer

3. **Merge**
   - Squash commits (optional)
   - Delete branch
   - Close related issues

## Release Process

Versions follow [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH`
- `1.0.0` - First stable release
- `1.1.0` - New feature
- `1.1.1` - Bug fix

## Architecture Decisions

Key architectural decisions:

- **Async/Await**: High concurrency support
- **SQLAlchemy ORM**: Type-safe database access
- **OAuth2**: Secure authentication
- **JWT Tokens**: Stateless sessions
- **Quart**: Async web framework
- **Pytest**: Comprehensive testing

## Resources

- [Python Best Practices](https://pep8.org/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Quart Docs](https://quart.palletsprojects.com/)
- [OAuth2 RFC](https://tools.ietf.org/html/rfc6749)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

Thank you for contributing! 🎉

**Last Updated**: February 24, 2026
