"""
Phase 2: Layered Dependencies
Dependencies: Phase 1

Tests dependency injection at three levels:
  app-level → pipeline-level → endpoint-level
Dependencies cascade from outer to inner, mirroring FastAPI's
  app(dependencies) → router(dependencies) → route(Depends)
"""

import fastapi
import pytest

from fastexec import FastExec, Pipeline


# --- 2.1 Endpoint-level dependencies (via Depends) ---


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


# --- 2.2 Pipeline-level dependencies ---


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


# --- 2.3 App-level dependencies ---


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


# --- 2.4 Cascading: app → pipeline → endpoint ---


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


# --- 2.5 Nested dependency chains across layers ---


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
