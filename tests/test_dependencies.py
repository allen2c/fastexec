"""
Dependencies: layered injection (app → pipeline → endpoint) and request-scope caching.
"""

import fastapi
import pytest

from fastexec import FastExec, Pipeline

# --- Endpoint-level dependencies ---


@pytest.mark.asyncio
async def test_endpoint_level_depends():
    """Endpoint functions can use fastapi.Depends() as usual."""
    app = FastExec()
    pipeline = Pipeline()

    def get_db():
        return "db_connection"

    async def get_users(db: str = fastapi.Depends(get_db)):
        return {"users": ["Alice"], "db": db}

    pipeline.register("/users", get_users)
    app.include_pipeline(pipeline)

    result = await app.exec("/users")
    assert result == {"users": ["Alice"], "db": "db_connection"}


# --- Pipeline-level dependencies ---


@pytest.mark.asyncio
async def test_pipeline_level_dependencies():
    """Pipeline-level dependencies are injected into all endpoints in that pipeline."""
    call_counts = {"auth": 0}

    def verify_auth():
        call_counts["auth"] += 1
        return "authenticated"

    pipeline = Pipeline(dependencies=[fastapi.Depends(verify_auth)])

    async def get_users(auth: str = fastapi.Depends(verify_auth)):
        return {"users": ["Alice"], "auth": auth}

    async def get_orders(auth: str = fastapi.Depends(verify_auth)):
        return {"orders": [1, 2], "auth": auth}

    pipeline.register("/users", get_users)
    pipeline.register("/orders", get_orders)

    app = FastExec()
    app.include_pipeline(pipeline)

    result = await app.exec("/users")
    assert result["auth"] == "authenticated"


# --- App-level dependencies ---


@pytest.mark.asyncio
async def test_app_level_dependencies():
    """App-level dependencies are injected into all pipelines."""
    call_counts = {"logging": 0}

    def setup_logging():
        call_counts["logging"] += 1
        return "logger_initialized"

    app = FastExec(dependencies=[fastapi.Depends(setup_logging)])
    pipeline = Pipeline()

    async def get_users(logging: str = fastapi.Depends(setup_logging)):
        return {"users": ["Alice"], "logging": logging}

    pipeline.register("/users", get_users)
    app.include_pipeline(pipeline)

    result = await app.exec("/users")
    assert result["logging"] == "logger_initialized"


# --- Cascading: app → pipeline → endpoint ---


@pytest.mark.asyncio
async def test_dependency_cascade():
    """Dependencies cascade from app → pipeline → endpoint, all available."""
    execution_order = []

    def app_dep():
        execution_order.append("app")
        return "app_value"

    def pipeline_dep():
        execution_order.append("pipeline")
        return "pipeline_value"

    def endpoint_dep():
        execution_order.append("endpoint")
        return "endpoint_value"

    app = FastExec(dependencies=[fastapi.Depends(app_dep)])
    pipeline = Pipeline(dependencies=[fastapi.Depends(pipeline_dep)])

    async def handler(
        a: str = fastapi.Depends(app_dep),
        p: str = fastapi.Depends(pipeline_dep),
        e: str = fastapi.Depends(endpoint_dep),
    ):
        return {"app": a, "pipeline": p, "endpoint": e}

    pipeline.register("/test", handler)
    app.include_pipeline(pipeline)

    result = await app.exec("/test")
    assert result == {
        "app": "app_value",
        "pipeline": "pipeline_value",
        "endpoint": "endpoint_value",
    }


# --- Nested dependency chains across layers ---


@pytest.mark.asyncio
async def test_nested_dependency_chain():
    """A pipeline dep can depend on an app dep, and endpoint dep on pipeline dep."""

    def get_config():
        return {"db_url": "sqlite:///test.db"}

    def get_db(config: dict = fastapi.Depends(get_config)):
        return f"connected:{config['db_url']}"

    async def get_users(db: str = fastapi.Depends(get_db)):
        return {"users": ["Alice"], "db": db}

    app = FastExec(dependencies=[fastapi.Depends(get_config)])
    pipeline = Pipeline(dependencies=[fastapi.Depends(get_db)])

    pipeline.register("/users", get_users)
    app.include_pipeline(pipeline)

    result = await app.exec("/users")
    assert result["db"] == "connected:sqlite:///test.db"


# --- Request-scope caching ---


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
