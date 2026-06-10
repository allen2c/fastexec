"""
Router: optional grouping with shared dependencies + prefix (= APIRouter).
"""

import fastapi
import pytest

from fastexec import FastExec, Router


@pytest.mark.asyncio
async def test_router_include_with_prefix():
    router = Router()

    @router.route("/list")
    async def list_users():
        return [{"id": 1}]

    app = FastExec()
    app.include_router(router, prefix="/users")

    assert await app.exec("/users/list") == [{"id": 1}]


@pytest.mark.asyncio
async def test_router_dependency_fires_during_exec():
    ran = []

    async def log():
        ran.append("router-dep")

    router = Router(dependencies=[fastapi.Depends(log)])

    @router.route("/p")
    async def p():
        return {"ok": True}

    app = FastExec()
    app.include_router(router, prefix="/v1")

    await app.exec("/v1/p")
    assert ran == ["router-dep"]
