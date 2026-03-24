"""
Phase 4: Dependency Caching (Request-Scope)
Dependencies: Phase 1, Phase 2

Tests that dependencies are cached within a single exec() call,
even when referenced by multiple layers or endpoints.
"""

import fastapi
import pytest

from fastexec import FastExec, Pipeline


# --- 4.1 Same dependency called once within single exec ---


@pytest.mark.asyncio
async def test_dependency_called_once():
    """A dependency used by multiple dependants is only called once per exec."""
    call_count = {"get_db": 0}

    def get_db():
        call_count["get_db"] += 1
        return "db_conn"

    def get_users(db: str = fastapi.Depends(get_db)):
        return {"users": ["Alice"], "db": db}

    def get_orders(db: str = fastapi.Depends(get_db)):
        return {"orders": [1], "db": db}

    async def handler(
        users: dict = fastapi.Depends(get_users),
        orders: dict = fastapi.Depends(get_orders),
    ):
        return {"users": users, "orders": orders}

    app = FastExec()
    pipeline = Pipeline()
    pipeline.register("/dashboard", handler)
    app.include_pipeline(pipeline)

    await app.exec("/dashboard")
    assert call_count["get_db"] == 1


# --- 4.2 Cache is NOT shared across exec calls ---


@pytest.mark.asyncio
async def test_cache_not_shared_across_execs():
    """Each exec() call gets a fresh dependency cache."""
    call_count = {"get_db": 0}

    def get_db():
        call_count["get_db"] += 1
        return "db_conn"

    async def handler(db: str = fastapi.Depends(get_db)):
        return {"db": db}

    app = FastExec()
    pipeline = Pipeline()
    pipeline.register("/test", handler)
    app.include_pipeline(pipeline)

    await app.exec("/test")
    await app.exec("/test")
    assert call_count["get_db"] == 2


# --- 4.3 Cross-layer caching ---


@pytest.mark.asyncio
async def test_cross_layer_dependency_cached():
    """A dependency referenced at both pipeline-level and endpoint-level is cached."""
    call_count = {"auth": 0}

    def verify_auth():
        call_count["auth"] += 1
        return "verified"

    pipeline = Pipeline(dependencies=[fastapi.Depends(verify_auth)])

    async def handler(auth: str = fastapi.Depends(verify_auth)):
        return {"auth": auth}

    pipeline.register("/secure", handler)

    app = FastExec()
    app.include_pipeline(pipeline)

    await app.exec("/secure")
    assert call_count["auth"] == 1


# --- 4.4 Deep dependency chain cached ---


@pytest.mark.asyncio
async def test_deep_chain_caching():
    """In a deep dependency DAG, each node is resolved exactly once."""
    call_counts = {
        "config": 0,
        "db": 0,
        "auth": 0,
        "resources": 0,
        "process": 0,
        "save": 0,
    }

    def get_config():
        call_counts["config"] += 1
        return {"db_url": "sqlite:///test.db", "api_key": "key123"}

    def get_db(config: dict = fastapi.Depends(get_config)):
        call_counts["db"] += 1
        return f"db:{config['db_url']}"

    def get_auth(config: dict = fastapi.Depends(get_config)):
        call_counts["auth"] += 1
        return f"auth:{config['api_key']}"

    def init_resources(
        db: str = fastapi.Depends(get_db),
        auth: str = fastapi.Depends(get_auth),
        config: dict = fastapi.Depends(get_config),
    ):
        call_counts["resources"] += 1
        return {"db": db, "auth": auth}

    def process_data(resources: dict = fastapi.Depends(init_resources)):
        call_counts["process"] += 1
        return {**resources, "processed": True}

    async def save_results(
        data: dict = fastapi.Depends(process_data),
        db: str = fastapi.Depends(get_db),
    ):
        call_counts["save"] += 1
        return {**data, "saved": True}

    app = FastExec()
    pipeline = Pipeline()
    pipeline.register("/run", save_results)
    app.include_pipeline(pipeline)

    result = await app.exec("/run")
    assert result["saved"] is True
    assert result["processed"] is True
    for name, count in call_counts.items():
        assert count == 1, f"{name} should be called exactly once, got {count}"
