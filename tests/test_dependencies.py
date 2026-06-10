"""
Dependency injection: app/endpoint deps, chains, yield teardown, request-scope cache.
"""

import fastapi
import pytest

from fastexec import FastExec


@pytest.mark.asyncio
async def test_app_dependency_fires():
    ran = []

    async def auth():
        ran.append("app-dep")

    app = FastExec(dependencies=[fastapi.Depends(auth)])

    @app.route("/p")
    async def p():
        return {"ok": True}

    await app.exec("/p")
    assert ran == ["app-dep"]


@pytest.mark.asyncio
async def test_dependency_chain_injection():
    def get_token(request: fastapi.Request):
        return "t"

    def get_user(token: str = fastapi.Depends(get_token)):
        return f"user-{token}"

    app = FastExec()

    @app.route("/me")
    async def me(user: str = fastapi.Depends(get_user)):
        return {"user": user}

    assert await app.exec("/me") == {"user": "user-t"}


@pytest.mark.asyncio
async def test_yield_dependency_teardown_runs():
    events = []

    async def resource():
        events.append("open")
        try:
            yield "r"
        finally:
            events.append("close")

    app = FastExec()

    @app.route("/r")
    async def r(res: str = fastapi.Depends(resource)):
        events.append("use")
        return {"res": res}

    await app.exec("/r")
    assert events == ["open", "use", "close"]


@pytest.mark.asyncio
async def test_request_scope_caching():
    calls = []

    def dep():
        calls.append(1)
        return len(calls)

    app = FastExec()

    @app.route("/c")
    async def c(a: int = fastapi.Depends(dep), b: int = fastapi.Depends(dep)):
        return {"a": a, "b": b}

    assert await app.exec("/c") == {"a": 1, "b": 1}
    assert len(calls) == 1
