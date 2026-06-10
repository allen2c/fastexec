"""
DI caching: per-route compilation is reused, not rebuilt per exec.
"""
import fastapi
import pydantic
import pytest

from fastexec import FastExec, Pipeline


@pytest.mark.asyncio
async def test_compiled_route_reused_across_calls():
    """Dependant and TypeAdapter are compiled once per route, then reused."""

    class Out(pydantic.BaseModel):
        id: int

    pipeline = Pipeline()

    @pipeline.register("/item", response_model=Out)
    async def item():
        return {"id": 1, "extra": "x"}

    app = FastExec()
    app.include_pipeline(pipeline)

    await app.exec("/item")
    dependant_first = app._compiled["/item"].dependant
    adapter_first = app._compiled["/item"].type_adapter

    await app.exec("/item")
    assert app._compiled["/item"].dependant is dependant_first
    assert app._compiled["/item"].type_adapter is adapter_first


@pytest.mark.asyncio
async def test_merged_dependant_not_mutated_across_calls():
    """Repeated exec must not regrow the merged dependency list (read-only reuse)."""

    async def guard():
        return None

    pipeline = Pipeline(dependencies=[fastapi.Depends(guard)])

    @pipeline.register("/p")
    async def handler():
        return {"ok": True}

    app = FastExec(dependencies=[fastapi.Depends(guard)])
    app.include_pipeline(pipeline)

    await app.exec("/p")
    n_first = len(app._compiled["/p"].dependant.dependencies)

    await app.exec("/p")
    await app.exec("/p")
    n_after = len(app._compiled["/p"].dependant.dependencies)

    assert n_after == n_first


@pytest.mark.asyncio
async def test_single_app_instance_reused():
    """One FastAPI instance is built per FastExec and reused across execs."""
    app = FastExec(state={"db": "x"})
    pipeline = Pipeline()

    @pipeline.register("/p")
    async def handler(request: fastapi.Request):
        return {"db": request.app.state.db}

    app.include_pipeline(pipeline)

    instance = app._app_instance
    result = await app.exec("/p")
    assert result == {"db": "x"}
    assert app._app_instance is instance
