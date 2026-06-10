# AGENTS.md

Guidance for AI agents and contributors working on **fastexec**. Keep changes small, tested, and idiomatic to the surrounding code.

## What fastexec is

Execute functions with FastAPI features — dependency injection, validation, response models, layered state — without an HTTP server. The public API is intentionally tiny: `FastExec` (app) and `Pipeline` (router), mirroring FastAPI's `FastAPI()` / `APIRouter`.

## Core principles

- **Mirror FastAPI.** Same mental model, same `Depends()` / `Query()` / type-hint validation. When unsure how something should behave, match FastAPI.
- **Reuse FastAPI internals** (`get_dependant`, `solve_dependencies`) instead of reimplementing them.
- **Minimal surface.** Keep each core module to ≤ 3 main exports. Don't add wrappers, type aliases, or helpers used in only one place — inline them.
- **No dead config.** A parameter that is accepted but never read is a bug, not a feature.

## Module layout

Order members within a module as:

1. Module docstring
2. Imports
3. Constants
4. Public functions
5. Public classes
6. Private functions / classes (if any)

When a private helper is referenced in a public signature, either define it before the public symbol or add `from __future__ import annotations` so the public-before-private order still holds.

## Boy Scout Rule

Always leave the code cleaner than you found it. When you touch a file, fix small adjacent issues — stale comments, a stale version string, dead code, a misnamed local — as part of your change. Stay within the scope of what you're already doing; don't start unrelated refactors.

## Tooling

- Python **3.11+**. Line length **88** everywhere.
- Format / lint is **isort + black + ruff**:
    - **black** formats (`target-version = py311`).
    - **isort** sorts imports (`profile = "black"`).
    - **ruff** lints only — `select = ["E", "F"]`, `ignore = ["E203"]`. Do **not** use `ruff format` or ruff's import sorting (`"I"`); they conflict with black/isort.
- Commands:
    - `make fmt` — isort → black → ruff check --fix
    - `make pytest` — run tests
    - `make install` — `pip install -e ".[dev,docs]"`
- The package version is a **static** string in `[project].version` and `fastexec/version.py` (kept in sync). `make update` uses `poetry update`, and Poetry rejects PEP 621 dynamic versions — do not switch to a dynamic/hatch version.

## Testing

- **TDD**: write a failing test first, run it to confirm it fails, implement the minimum to pass, then refactor.
- Name test files by **feature** (`test_core.py`, `test_dependencies.py`), never by phase or version.
- `pytest-asyncio` runs in auto mode. Long memory/leak tests use `@pytest.mark.stress` and are skipped by default; run them with `pytest -m stress`.
- All existing tests passing is the regression gate for any refactor — behaviour-preserving changes must keep the suite green.

## Git

- Work on `dev/<version>` branches (e.g. `dev/v0.7.0`).
- Do **not** commit to `main`, push, or otherwise touch `origin` without explicit permission for that task. Creating a branch off `main` is fine; committing to it is not.
