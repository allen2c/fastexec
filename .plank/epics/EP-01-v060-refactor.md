---
id: EP-01
title: v0.6.0 Architecture Refactor
status: todo
created: 2026-03-24
updated: 2026-03-24
---

# v0.6.0 Architecture Refactor

## Overview

Major breaking-change refactor of fastexec to align with FastAPI's architectural patterns. The goal is to provide a familiar mental model for FastAPI users: a central `FastExec` app object that includes `Pipeline` objects (analogous to `APIRouter`), each with path-based dispatch, layered dependency injection, and full FastAPI response/exception compatibility.

Key design decisions:
- **Breaking change** — no backward compatibility with v0.5.x API
- **Layered dependencies**: `FastExec` (app) → `Pipeline` → endpoint, cascading from outer to inner
- **Path-based dispatch**: endpoints are registered with paths, `app.exec("/path")` dispatches
- **FastAPI compatibility**: same exceptions, response models, auto-validation via type hints
- **Reuse FastAPI internals**: `solve_dependencies`, `get_dependant`, routing dispatch

Architecture mapping:

| FastAPI         | fastexec v0.6.0                          |
|-----------------|------------------------------------------|
| `FastAPI()`     | `FastExec(state=, dependencies=)`        |
| `APIRouter`     | `Pipeline(dependencies=)`                |
| `router.get()`  | `pipeline.register("/path", fn)`         |
| `app.include_router()` | `app.include_pipeline(pipeline, prefix=)` |
| `Depends()`     | `fastapi.Depends()` (reused directly)    |
| Request/Response | FastAPI-compatible mock request context  |

## Issues

| ID     | Title                                              | Status |
|--------|----------------------------------------------------|--------|
| FE-001 | Implement FastExec and Pipeline core skeleton      | todo   |
| FE-002 | Implement layered dependency injection             | todo   |
| FE-003 | Implement state management                         | todo   |
| FE-004 | Implement request-scope dependency caching         | todo   |
| FE-005 | Implement request parameter passing                | todo   |
| FE-006 | Implement nested pipelines and advanced features   | todo   |
| FE-007 | Implement FastAPI response and exception compat    | todo   |
| FE-008 | Implement auto validation via type hints           | todo   |
| FE-009 | Remove legacy API and finalize breaking changes    | todo   |

## Notes

Test-first approach: all 54 dummy tests across 8 phases are written in `tests/v060/` before implementation begins. Each issue corresponds to one phase of tests.
