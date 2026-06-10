"""
Memory leak stress test (manual): `pytest -m stress`.

Runs ~90k exec() calls covering a yield dependency, a response_model,
and two error paths (HTTPException + RequestValidationError), then asserts
RSS and GC-tracked object counts stay flat between two post-warmup checkpoints.
"""

import gc

import fastapi
import fastapi.exceptions
import psutil
import pydantic
import pytest

from fastexec import FastExec, Pipeline


def _rss_mb() -> float:
    return psutil.Process().memory_info().rss / (1024 * 1024)


def _build_app() -> FastExec:
    pipeline = Pipeline()

    async def yield_dep():
        resource = {"open": True}
        try:
            yield resource
        finally:
            resource["open"] = False

    class ItemOut(pydantic.BaseModel):
        id: int
        name: str

    @pipeline.register("/ok", response_model=ItemOut)
    async def ok(
        name: str = fastapi.Query("x"),
        res: dict = fastapi.Depends(yield_dep),
    ):
        return {"id": 1, "name": name, "extra": "strip"}

    @pipeline.register("/boom")
    async def boom():
        raise fastapi.HTTPException(status_code=400, detail="boom")

    @pipeline.register("/invalid")
    async def invalid(n: int = fastapi.Query(...)):
        return {"n": n}

    app = FastExec()
    app.include_pipeline(pipeline)
    return app


async def _hit_all(app: FastExec) -> None:
    await app.exec("/ok", query_params={"name": "a"})
    try:
        await app.exec("/boom")
    except fastapi.HTTPException:
        pass
    try:
        await app.exec("/invalid")  # missing required query -> validation error
    except fastapi.exceptions.RequestValidationError:
        pass


@pytest.mark.stress
@pytest.mark.asyncio
async def test_exec_does_not_leak():
    app = _build_app()

    # Warm up: compile caches + allocator steady state.
    for _ in range(2000):
        await _hit_all(app)
    gc.collect()
    rss_checkpoint_1 = _rss_mb()
    objs_checkpoint_1 = len(gc.get_objects())

    for _ in range(30000):
        await _hit_all(app)
    gc.collect()
    rss_checkpoint_2 = _rss_mb()
    objs_checkpoint_2 = len(gc.get_objects())

    rss_growth = rss_checkpoint_2 - rss_checkpoint_1
    obj_growth = objs_checkpoint_2 - objs_checkpoint_1

    # Slope between two post-warmup checkpoints must be ~flat.
    # Thresholds are starting points — tune if the environment is noisy.
    assert rss_growth < 5.0, f"RSS grew {rss_growth:.2f} MB between checkpoints"
    assert obj_growth < 2000, f"GC-tracked objects grew by {obj_growth}"
