"""
Inputs: query, body, headers, path params; sync endpoints; validation errors.
"""

import fastapi
import fastapi.exceptions
import pydantic
import pytest

from fastexec import FastExec


@pytest.mark.asyncio
async def test_path_params():
    app = FastExec()

    @app.route("/items/{item_id}")
    async def get_item(item_id: int):
        return {"id": item_id}

    assert await app.exec("/items/42") == {"id": 42}


@pytest.mark.asyncio
async def test_body_pydantic_model():
    class In(pydantic.BaseModel):
        name: str

    app = FastExec()

    @app.route("/create")
    async def create(payload: In):
        return {"name": payload.name}

    assert await app.exec("/create", body={"name": "Alice"}) == {"name": "Alice"}


@pytest.mark.asyncio
async def test_headers():
    app = FastExec()

    @app.route("/h")
    async def h(x_token: str = fastapi.Header(...)):
        return {"token": x_token}

    assert await app.exec("/h", headers={"x-token": "abc"}) == {"token": "abc"}


@pytest.mark.asyncio
async def test_sync_endpoint():
    app = FastExec()

    @app.route("/s")
    def s():
        return {"mode": "sync"}

    assert await app.exec("/s") == {"mode": "sync"}


@pytest.mark.asyncio
async def test_missing_required_input_raises():
    app = FastExec()

    @app.route("/need")
    async def need(n: int = fastapi.Query(...)):
        return {"n": n}

    with pytest.raises(fastapi.exceptions.RequestValidationError):
        await app.exec("/need")
