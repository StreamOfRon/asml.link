TL;DR — Add three GitHub configs: PR checks to run tests/lint on pull requests, Dependabot to auto-propose dependency updates, and a Docker publish workflow that builds the production image and pushes to GitHub Container Registry on merges to `main`. This uses existing scripts/commands (`uv run pytest`, `uv run lint`, `uv run format`), the repo `Dockerfile`, and `uv`/`uv.lock`. Key decisions: target branch `main`, publish to `ghcr.io`, and tag images with commit SHA + `latest`.

Steps
1. Add Dependabot config: create `.github/dependabot.yml` to scan Python dependencies weekly and optionally Docker/GitHub Actions updates. See `pyproject.toml` and `uv.lock` for package sources.
2. Add PR checks workflow: create `.github/workflows/pr-checks.yml` triggered on `pull_request` (events: `opened`, `synchronize`, `reopened`), matrix on supported Python versions (recommend 3.10, 3.11, 3.12), steps:
   - Checkout repository.
   - Setup Python (matching matrix).
   - Cache pip and potentially `uv` caches.
   - Install `uv` (pip) and run `uv sync --no-dev` (or `uv sync` if dev deps wanted for tests).
   - Run tests: `uv run pytest` (or the tests script: `uv run pytest tests/ -v --cov=app --cov-report=term-missing`).
   - Run linters/typechecks: `uv run lint` (which runs `ruff` and `mypy`) and run formatting checks (e.g., `uv run format` in check mode / `black --check` and `ruff check`).
   - Upload test artifacts and coverage report as workflow artifacts.
   - Use `permissions: contents: read` (default) and no extra secrets required.
   - Files to reference: `scripts/test.sh`, `scripts/lint.sh`, `scripts/format.sh`, `pyproject.toml`.
3. Add Docker publish workflow: create `.github/workflows/docker-publish.yml` triggered on `push` to `main` and `workflow_dispatch`, steps:
   - Require `permissions: packages: write` (so `GITHUB_TOKEN` can push to GHCR).
   - Checkout repo.
   - Login to ghcr.io using `docker/login-action` with `username: ${{ github.actor }}` and `password: ${{ secrets.GITHUB_TOKEN }}`.
   - Build multi-stage production image using the repository `Dockerfile` with `--target production` (or the production stage name), tag image as `ghcr.io/${{ github.repository_owner }}/asml.link:${{ github.sha }}` and `ghcr.io/${{ github.repository_owner }}/asml.link:latest`.
   - Push both tags to GHCR.
   - Optionally create a release entry or add post-publish notification.
   - Files to reference: `Dockerfile`, `DEPLOYMENT.md`.
4. CI details and caching:
   - Cache pip wheels and the pip cache between runs (`actions/cache` on `~/.cache/pip`).
   - Consider caching `uv` artifacts if heavy; otherwise rely on `uv sync` each run.
   - Use matrix caching keys so different Python versions use distinct caches.
5. Secrets/Permissions:
   - For GHCR: use `GITHUB_TOKEN` with workflow-level `permissions: packages: write`. No additional secrets required by default.
   - Document optional PAT flow if org policies require a token with broader permissions.
6. Documentation/update:
   - Add a short note in `AGENTS.md` or `README.md` describing the CI and publish process and required repo settings (GHCR package write permission).
   - Add a `.github/ISSUE_TEMPLATE` or PR checklist (optional) to remind contributors to run `uv run format` locally.
7. Verification plan:
   - Local: run `uv run pytest`, `uv run lint`, `uv run format` (check mode), and `docker build --target production -t local:prod .`.
   - After pushing workflow files to a feature branch: open a PR and verify `pr-checks` runs and passes on the PR.
   - Merge to `main` (or run `workflow_dispatch`) and verify `docker-publish` builds and pushes to GHCR. Confirm image tags `sha` and `latest` appear in GHCR UI.

Decisions
- Branch: publish on merges to `main` (user requested `master` but repo default is `main`).
- Registry: GitHub Container Registry (`ghcr.io`) using `GITHUB_TOKEN` and workflow `permissions: packages: write`.
- Tagging: push `ghcr.io/<owner>/asml.link:<commit-sha>` plus `ghcr.io/<owner>/asml.link:latest`.

Verification
- Locally run: `uv run pytest` and `uv run lint`.
- Verify format check: `uv run format` (or `black --check` + `ruff check`).
- Build image locally: `docker build --target production -t local-asml:prod .`.
- Create a test PR to confirm `pr-checks` runs; push to `main` to confirm `docker-publish`.

Next steps
- I can scaffold the workflow and dependabot files now. Want me to add them to `.github/`?
