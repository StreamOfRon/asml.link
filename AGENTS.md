# OpenCode Agents Guide

This document describes how to use OpenCode agents effectively for this Link Shortening Service project.

## Available Agents

### 1. Explore Agent
**Use case**: Quickly understand codebase structure, find files, search for patterns

**When to use**:
- Identify where specific functionality is implemented
- Find all files related to a feature (e.g., "Where is OAuth handled?")
- Search for code patterns across the project
- Understand component relationships
- Answer "how does X work?" questions

**Example prompts**:
```
Find all files that handle database queries and identify N+1 query problems
Locate all middleware files and explain their responsibilities
Search for all rate limiting implementation and how it's used
```

**Thoroughness levels**:
- `quick`: Basic file finding and simple pattern searches
- `medium`: Search across multiple locations, understand relationships
- `very_thorough`: Comprehensive analysis including test coverage, edge cases, integration points

---

### 2. General Agent
**Use case**: Execute complex multi-step tasks, run tests, make changes, verify results

**When to use**:
- Implement new features or bug fixes
- Run test suites and fix failures
- Refactor code sections
- Performance optimization work
- Complex debugging scenarios
- Multi-file changes

**Example prompts**:
```
Add caching to the LinkService to reduce database queries. Verify with tests.
Implement database connection pooling optimization and measure performance improvements
Fix all pytest failures in the test suite
```

---

## Common Tasks & Recommended Agents

| Task | Agent | Notes |
|------|-------|-------|
| Find where something is implemented | Explore | Use `quick` for simple files, `very_thorough` for complex features |
| Understand how a component works | Explore | Use `medium` or `very_thorough` |
| Add a new feature | General | Combines research + implementation + testing |
| Fix a bug | General | Search first with Explore, then fix with General |
| Performance optimization | General | Analyze with Explore first, optimize with General |
| Run and fix tests | General | Can handle entire test suite execution and fixes |
| Refactor code | General | Complex multi-step changes across files |
| Security audit | Explore | Find security-related code, then General for fixes |

---

## Project Structure Reference

Understanding the project layout helps you ask better agent questions:

```
app/
├── models/          # SQLAlchemy ORM models (User, Link, OAuthAccount, etc.)
├── services/        # Business logic layer (LinkService, UserService, etc.)
├── routes/          # API endpoints and web UI routes
├── middleware/      # Request/response middleware (CSRF, Security, Error Handling)
├── schemas/         # Pydantic request/response validation
├── utils/           # Helper functions (validators, slug generator, OAuth)
├── templates/       # Jinja2 HTML templates
└── static/          # CSS, JavaScript, static assets

tests/               # 344+ tests covering all functionality
migrations/          # Alembic database migrations
```

---

## Example Workflows

### Workflow 1: Add a Performance Optimization Feature

1. **Use Explore Agent** (`very_thorough`)
   ```
   Analyze the LinkService for N+1 query problems and identify caching opportunities
   ```

2. **Review results** and understand the optimization needs

3. **Use General Agent**
   ```
   Implement Redis caching for frequently accessed links. Update LinkService.get_link()
   to check cache first. Add cache invalidation on link updates. Ensure all tests pass.
   ```

4. **Verify** by running tests and checking performance metrics

---

### Workflow 2: Understand a Complex System

1. **Use Explore Agent** (`medium`)
   ```
   How does the OAuth authentication flow work? Find all OAuth-related files and explain the flow.
   ```

2. **Review output** to understand the flow

3. **Use General Agent** if changes needed
   ```
   Add support for a new OAuth provider (Microsoft). Follow the existing Google/GitHub pattern.
   ```

---

### Workflow 3: Fix Performance Issues

1. **Use Explore Agent** (`very_thorough`)
   ```
   Identify slow database queries in the admin dashboard endpoints. Find all SELECT queries
   that might have N+1 problems. Check for missing indexes.
   ```

2. **Review recommendations**

3. **Use General Agent**
   ```
   Optimize the identified slow queries by adding proper joins and indexes.
   Measure performance improvements and verify tests still pass.
   ```

---

## Performance Optimization Opportunities

The project has identified the following optimization categories:

- **Database Queries**: N+1 queries, missing indexes, inefficient joins
- **Caching**: Frequently accessed data (links, user info), expensive computations
- **Rate Limiter**: Current database lookups on every request
- **Session Management**: Connection pooling efficiency
- **API Responses**: Minimize data fetching and serialization
- **Static Assets**: Compression and caching headers

**Use this agent command to analyze all opportunities:**

```
Use the Explore agent (very_thorough) to identify all performance optimization
opportunities in the codebase, with specific files, line numbers, and severity levels.
```

---

## Tips for Effective Agent Usage

### ✅ DO:
- Be specific about what you want to understand or change
- Include file paths or feature names in your query
- Ask agents to verify their work with tests
- Use `very_thorough` when exploring complex interconnected code
- Ask agents to explain what they found before making changes

### ❌ DON'T:
- Use agents for trivial single-file changes (just edit directly)
- Ask vague questions without context
- Assume agents will find every edge case without explicit instructions
- Use General agent for pure research (use Explore instead)
- Forget to run tests after making changes

---

## Security & Compliance Features to Maintain

When using agents for changes, ensure these remain intact:

- **CSRF Protection** (middleware/csrf.py)
- **Security Headers** (middleware/security_headers.py)
- **Rate Limiting** (services/rate_limiter.py)
- **Input Validation** (utils/validators.py)
- **JWT Token Handling** (services/auth_service.py)
- **OAuth Provider Safety** (utils/oauth.py)
- **Database Query Safety** (services/models)

Ask agents to verify these features are maintained after optimization changes.

---

## Resources

- **README.md** - Project overview and quick start
- **CONFIGURATION.md** - Environment variables and setup
- **DEPLOYMENT.md** - Production deployment guide
- **CONTRIBUTING.md** - Development workflow and testing
- **Test Suite** - 344+ tests in `tests/` directory (run with `pytest`)
- **Git History** - Check commits for implementation details

---

## Questions?

For OpenCode documentation: https://opencode.ai/docs
