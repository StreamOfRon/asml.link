<!-- Title: Short, descriptive PR title -->

## Summary
A short description of what this PR does and why.

## Related Issues
- Fixes / relates to: # (issue number)

## Changes
- Bullet list of changes made

## How to test
1. Run `uv sync`
2. Run tests: `uv run pytest`
3. Run linters: `uv run lint`
4. (Optional) Build image: `docker build --target production -t local-asml:prod .`

## Checklist
- [ ] I have run `uv run format` and committed formatting changes
- [ ] I have run `uv run lint` and addressed all findings
- [ ] I have run tests locally (`uv run pytest`) and they pass
- [ ] I added/updated tests for any new behavior
- [ ] I updated relevant documentation (README, AGENTS.md, CONFIGURATION.md)

## Notes
Add any additional notes for reviewers, edge-cases, or deployment considerations.
