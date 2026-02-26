<!-- Title: Short, descriptive PR title -->

## Summary
A short description of what this PR does and why.

## Related Issues
- Fixes / relates to: # (issue number)

## Changes
- Bullet list of changes made

## How to test
1. Run `uv sync`
2. Run tests: `./scripts/test.sh`
3. Run linters: `./scripts/lint.sh`
4. (Optional) Build image: `docker build --target production -t local-asml:prod .`

## Checklist
- [ ] I have run `./scripts/lint.sh` and addressed all findings
- [ ] I have run `./scripts/test.sh` and tests pass
- [ ] Type hints are present in new or changed code
- [ ] I added/updated tests for any new behavior
- [ ] I updated relevant documentation (README, AGENTS.md, CONFIGURATION.md)

## Notes
Add any additional notes for reviewers, edge-cases, or deployment considerations.

---

**Python version required: 3.11+**
