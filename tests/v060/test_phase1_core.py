"""
Phase 1: Core Skeleton
Dependencies: None (foundation)

Tests the basic FastExec + Pipeline + registration + dispatch flow.
"""

import pytest

from fastexec import FastExec, Pipeline

# --- 1.1 FastExec instantiation ---


@pytest.mark.asyncio
async def test_fastexec_creation():
    """FastExec can be instantiated as the central app object."""
    app = FastExec()
    assert app is not None


@pytest.mark.asyncio
async def test_fastexec_creation_with_state():
    """FastExec accepts initial app-level state."""
    app = FastExec(state={"db": "sqlite:///test.db"})
    assert app.state.db == "sqlite:///test.db"


# --- 1.2 Pipeline instantiation ---


@pytest.mark.asyncio
async def test_pipeline_creation():
    """Pipeline can be instantiated independently."""
    pipeline = Pipeline()
    assert pipeline is not None


# --- 1.3 Registering endpoints on Pipeline ---


@pytest.mark.asyncio
async def test_pipeline_register_function():
    """Pipeline can register a callable with a path."""
    pipeline = Pipeline()

    async def get_users():
        return [{"id": 1, "name": "Alice"}]

    pipeline.register("/users", get_users)


@pytest.mark.asyncio
async def test_pipeline_register_decorator():
    """Pipeline supports decorator syntax for registration."""
    pipeline = Pipeline()

    @pipeline.register("/users")
    async def get_users():
        return [{"id": 1, "name": "Alice"}]


# --- 1.4 Including Pipeline in FastExec ---


@pytest.mark.asyncio
async def test_include_pipeline():
    """FastExec can include a pipeline."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_users():
        return [{"id": 1, "name": "Alice"}]

    pipeline.register("/users", get_users)
    app.include_pipeline(pipeline)


@pytest.mark.asyncio
async def test_include_pipeline_with_prefix():
    """FastExec can include a pipeline with a path prefix."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_users():
        return [{"id": 1, "name": "Alice"}]

    pipeline.register("/users", get_users)
    app.include_pipeline(pipeline, prefix="/api/v1")


# --- 1.5 Dispatch via exec ---


@pytest.mark.asyncio
async def test_exec_dispatches_by_path():
    """app.exec() dispatches to the correct endpoint by path."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_users():
        return [{"id": 1, "name": "Alice"}]

    async def get_orders():
        return [{"id": 100, "item": "Widget"}]

    pipeline.register("/users", get_users)
    pipeline.register("/orders", get_orders)
    app.include_pipeline(pipeline)

    result = await app.exec("/users")
    assert result == [{"id": 1, "name": "Alice"}]

    result = await app.exec("/orders")
    assert result == [{"id": 100, "item": "Widget"}]


@pytest.mark.asyncio
async def test_exec_with_prefix_dispatches_correctly():
    """Prefix + path combines for dispatch."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_users():
        return [{"id": 1, "name": "Alice"}]

    pipeline.register("/users", get_users)
    app.include_pipeline(pipeline, prefix="/api/v1")

    result = await app.exec("/api/v1/users")
    assert result == [{"id": 1, "name": "Alice"}]


@pytest.mark.asyncio
async def test_exec_sync_function():
    """app.exec() handles sync functions transparently."""
    app = FastExec()
    pipeline = Pipeline()

    def get_users():
        return [{"id": 1, "name": "Alice"}]

    pipeline.register("/users", get_users)
    app.include_pipeline(pipeline)

    result = await app.exec("/users")
    assert result == [{"id": 1, "name": "Alice"}]


@pytest.mark.asyncio
async def test_exec_unknown_path_raises():
    """app.exec() raises an error for unregistered paths."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_users():
        return []

    pipeline.register("/users", get_users)
    app.include_pipeline(pipeline)

    with pytest.raises(LookupError):
        await app.exec("/nonexistent")
