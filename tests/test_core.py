"""
Core: define a workflow with @app.route and run it with exec().
"""

import fastapi
import pydantic
import pytest

from fastexec import FastExec


@pytest.mark.asyncio
async def test_route_on_app_and_exec():
    app = FastExec()

    @app.route("/greet")
    async def greet(name: str = fastapi.Query("World")):
        return {"message": f"Hello, {name}!"}

    result = await app.exec("/greet", query_params={"name": "Alice"})
    assert result == {"message": "Hello, Alice!"}


@pytest.mark.asyncio
async def test_response_model_filters_fields():
    class Out(pydantic.BaseModel):
        id: int
        name: str

    app = FastExec()

    @app.route("/item", response_model=Out)
    async def item():
        return {"id": 1, "name": "Widget", "secret": "strip"}

    assert await app.exec("/item") == {"id": 1, "name": "Widget"}


@pytest.mark.asyncio
async def test_unknown_path_raises_lookuperror():
    app = FastExec()
    with pytest.raises(LookupError):
        await app.exec("/nope")


@pytest.mark.asyncio
async def test_exec_needs_no_warmup():
    # route.dependant exists at registration -> no prior call needed
    app = FastExec()

    @app.route("/x")
    async def x():
        return {"ok": True}

    assert await app.exec("/x") == {"ok": True}


def test_public_api_drops_pipeline():
    import fastexec

    assert "FastExec" in fastexec.__all__
    assert not hasattr(fastexec, "Pipeline")
