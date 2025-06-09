# Shell Command History - Session 2025-06-06_15-23

## 2025-06-06

```bash
uv run ruff . && uv run mypy . && uv run -m pytest -q
# initial attempt to run linters and tests, but ruff CLI requires 'check' subcommand; command failed
```bash
uv run ruff check . && uv run mypy . && uv run -m pytest -q
# retried linting and tests with correct ruff subcommand; failures pre-existing, unrelated to .gitignore update
```