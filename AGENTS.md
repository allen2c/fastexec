# AGENTS.md

Guidance for AI agents and contributors working on **fastexec**. Keep changes small, tested, and idiomatic to the surrounding code.

## What fastexec is

A **serverless workflow engine** whose DAG executor *is* FastAPI's dependency injection: a `Depends()` is a node's input edge, the return value is its output, the dependency graph is the workflow DAG, and `exec(path, ...)` runs it in-process — no HTTP server. The public API is intentionally tiny: `FastExec` (app) and `Router` (optional grouping).

fastexec **subclasses FastAPI**: `FastExec(FastAPI)` (`_app.py`), `Router(APIRouter)` + a `_RouteMixin.route()` verbless decorator (`_routing.py`). `exec()` finds a route via Starlette matching and runs `solve_dependencies` over the route's native `.dependant` (FastAPI already merges app + router + endpoint deps).

**Optional add-ons live in their own module behind an extra.** `fastexec.viz` (a workflow-diagram renderer) is used via `from fastexec import viz`, lazy-imports `graphviz`, and is declared under the `viz` extra — so core never depends on it and `__all__` stays `FastExec` / `Router`. Follow this pattern for any heavy/optional dependency.

## Core principles

- **Be FastAPI.** Inherit FastAPI's objects; behaviour is 100% FastAPI. When unsure how something should behave, it behaves the way FastAPI does.
- **Don't reinvent what FastAPI lacks.** No custom DAG executor, no parallel node execution, no per-task retries/timeouts. If FastAPI doesn't do it, fastexec doesn't either — that keeps it a thin, honest layer (not Airflow/Prefect).
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
- `pytest-asyncio` runs in auto mode.
- All existing tests passing is the regression gate for any refactor — behaviour-preserving changes must keep the suite green.

## Git

- Work on `dev/<version>` branches (e.g. `dev/v0.7.0`).
- Do **not** commit to `main`, push, or otherwise touch `origin` without explicit permission for that task. Creating a branch off `main` is fine; committing to it is not.
