"""
Phase 3: State Management
Dependencies: Phase 1

Tests app state and request state access across layers.
"""

import fastapi
import pytest

from fastexec import FastExec, Pipeline


# --- 3.1 App state ---


@pytest.mark.asyncio
async def test_app_state_accessible_in_endpoint():
    """Endpoints can access app.state via request.app.state."""
    app = FastExec(state={"app_name": "TestApp", "version": "1.0"})
    pipeline = Pipeline()

    async def get_info(request: fastapi.Request):
        return {
            "app_name": request.app.state.app_name,
            "version": request.app.state.version,
        }

    pipeline.register("/info", get_info)
    app.include_pipeline(pipeline)

    result = await app.exec("/info")
    assert result == {"app_name": "TestApp", "version": "1.0"}


# --- 3.2 Request state ---


@pytest.mark.asyncio
async def test_request_state_per_exec():
    """Each exec() call can pass request-scoped state."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_session(request: fastapi.Request):
        return {"session_id": request.state.session_id}

    pipeline.register("/session", get_session)
    app.include_pipeline(pipeline)

    result = await app.exec("/session", state={"session_id": "abc-123"})
    assert result == {"session_id": "abc-123"}


# --- 3.3 App state + request state coexist ---


@pytest.mark.asyncio
async def test_app_state_and_request_state_coexist():
    """Both app state and request state are accessible simultaneously."""
    app = FastExec(state={"db": "postgres://localhost"})
    pipeline = Pipeline()

    async def handler(request: fastapi.Request):
        return {
            "db": request.app.state.db,
            "user_id": request.state.user_id,
        }

    pipeline.register("/check", handler)
    app.include_pipeline(pipeline)

    result = await app.exec("/check", state={"user_id": "user-42"})
    assert result == {"db": "postgres://localhost", "user_id": "user-42"}


# --- 3.4 State accessible in dependencies ---


@pytest.mark.asyncio
async def test_state_accessible_in_dependencies():
    """Dependencies (not just endpoints) can access state via request."""
    app = FastExec(state={"secret_key": "s3cret"})
    pipeline = Pipeline()

    def get_auth(request: fastapi.Request):
        return f"auth_with_{request.app.state.secret_key}"

    async def handler(auth: str = fastapi.Depends(get_auth)):
        return {"auth": auth}

    pipeline.register("/secure", handler)
    app.include_pipeline(pipeline)

    result = await app.exec("/secure")
    assert result == {"auth": "auth_with_s3cret"}


# --- 3.5 State isolation between exec calls ---


@pytest.mark.asyncio
async def test_request_state_isolated_between_execs():
    """Request state from one exec() does not leak into another."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_session(request: fastapi.Request):
        return {"session_id": request.state.session_id}

    pipeline.register("/session", get_session)
    app.include_pipeline(pipeline)

    result1 = await app.exec("/session", state={"session_id": "session-1"})
    result2 = await app.exec("/session", state={"session_id": "session-2"})

    assert result1 == {"session_id": "session-1"}
    assert result2 == {"session_id": "session-2"}
