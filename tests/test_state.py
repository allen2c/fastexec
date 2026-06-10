"""
State: native app.state and per-exec request.state.
"""

import fastapi
import pytest

from fastexec import FastExec


@pytest.mark.asyncio
async def test_app_state_is_native():
    app = FastExec()
    app.state.db = "sqlite://x"

    @app.route("/db")
    async def db(request: fastapi.Request):
        return {"db": request.app.state.db}

    assert await app.exec("/db") == {"db": "sqlite://x"}


@pytest.mark.asyncio
async def test_per_exec_state():
    app = FastExec()

    @app.route("/s")
    async def s(request: fastapi.Request):
        return {"sid": request.state.sid}

    assert await app.exec("/s", state={"sid": "abc"}) == {"sid": "abc"}
