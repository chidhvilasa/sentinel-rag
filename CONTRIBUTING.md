# Contributing to Sentinel-RAG

Thanks for your interest in contributing. This is an active research project — contributions that improve detection coverage, fix bugs, or improve documentation/tooling are all welcome.

## Getting started

1. Fork the repo and clone your fork.
2. Follow [`docs/installation.md`](docs/installation.md) to set up your environment.
3. Install dev dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
4. Create a branch: `git checkout -b my-change`

## Making changes

- Keep detection/neutralization changes and infrastructure/docs changes in separate PRs where possible — they're reviewed differently.
- If you're adding or changing a detection pattern, add a test case in `tests/test_detector.py` or `tests/test_neutralizer.py` and, ideally, a sample in `data/poisoned/`.
- Run the test suite and linters before opening a PR:
  ```bash
  pytest tests/
  ruff check .
  black --check .
  isort --check-only .
  ```
  CI (`.github/workflows/`) runs these same checks, plus `bandit`/`pip-audit`/secret scanning, on every PR.
- If your change affects detection accuracy or latency, re-run the relevant script in `scripts/` (see [`docs/benchmarks.md`](docs/benchmarks.md)) and mention the before/after numbers in your PR description.

## Commit messages

Keep them descriptive and focused on *why*, not just *what*. Small, focused commits are easier to review than one large commit.

## Reporting bugs / requesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`. For security vulnerabilities, see [`SECURITY.md`](SECURITY.md) instead of opening a public issue.

## Code style

- Python 3.10+, formatted with `black`, linted with `ruff` (see `pyproject.toml` for config).
- Prefer explicit, readable code over cleverness — this is a security-relevant codebase and clarity matters more than brevity.

## Pull requests

- Fill out the PR template.
- Link any related issue.
- Expect at least one round of review before merge.
