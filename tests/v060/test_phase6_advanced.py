"""
Phase 6: Advanced Features
Dependencies: Phase 1-5

Tests nested pipelines, multiple pipelines, and decorator patterns.
"""

import fastapi
import pytest

from fastexec import FastExec, Pipeline


# --- 6.1 Multiple pipelines ---


@pytest.mark.asyncio
async def test_multiple_pipelines():
    """Multiple pipelines can coexist under different prefixes."""
    app = FastExec()

    users_pipeline = Pipeline()
    orders_pipeline = Pipeline()

    async def get_users():
        return {"resource": "users"}

    async def get_orders():
        return {"resource": "orders"}

    users_pipeline.register("/list", get_users)
    orders_pipeline.register("/list", get_orders)

    app.include_pipeline(users_pipeline, prefix="/users")
    app.include_pipeline(orders_pipeline, prefix="/orders")

    assert await app.exec("/users/list") == {"resource": "users"}
    assert await app.exec("/orders/list") == {"resource": "orders"}


# --- 6.2 Nested pipelines (sub-pipelines) ---


@pytest.mark.asyncio
async def test_nested_pipelines():
    """A pipeline can include sub-pipelines, like FastAPI's nested routers."""
    app = FastExec()

    parent = Pipeline()
    child = Pipeline()

    async def get_items():
        return {"items": [1, 2, 3]}

    child.register("/items", get_items)
    parent.include_pipeline(child, prefix="/v2")

    app.include_pipeline(parent, prefix="/api")

    result = await app.exec("/api/v2/items")
    assert result == {"items": [1, 2, 3]}


# --- 6.3 Pipeline-isolated dependencies ---


@pytest.mark.asyncio
async def test_pipelines_have_isolated_dependencies():
    """Different pipelines can have different pipeline-level dependencies."""
    app = FastExec()

    def admin_auth():
        return "admin"

    def user_auth():
        return "user"

    admin_pipeline = Pipeline(dependencies=[fastapi.Depends(admin_auth)])
    user_pipeline = Pipeline(dependencies=[fastapi.Depends(user_auth)])

    async def admin_handler(role: str = fastapi.Depends(admin_auth)):
        return {"role": role}

    async def user_handler(role: str = fastapi.Depends(user_auth)):
        return {"role": role}

    admin_pipeline.register("/dashboard", admin_handler)
    user_pipeline.register("/profile", user_handler)

    app.include_pipeline(admin_pipeline, prefix="/admin")
    app.include_pipeline(user_pipeline, prefix="/user")

    assert (await app.exec("/admin/dashboard"))["role"] == "admin"
    assert (await app.exec("/user/profile"))["role"] == "user"


# --- 6.4 Decorator with all features combined ---


@pytest.mark.asyncio
async def test_full_integration():
    """Full integration: app state + pipeline deps + endpoint deps + params."""
    call_counts = {"config": 0, "db": 0, "auth": 0}

    def get_config():
        call_counts["config"] += 1
        return {"db_url": "sqlite:///prod.db"}

    def get_db(config: dict = fastapi.Depends(get_config)):
        call_counts["db"] += 1
        return f"db:{config['db_url']}"

    def verify_auth(request: fastapi.Request):
        call_counts["auth"] += 1
        return f"auth:{request.app.state.secret}"

    app = FastExec(
        state={"secret": "s3cret"},
        dependencies=[fastapi.Depends(get_config)],
    )

    pipeline = Pipeline(dependencies=[fastapi.Depends(verify_auth)])

    @pipeline.register("/users")
    async def get_users(
        request: fastapi.Request,
        q: str = fastapi.Query(default=""),
        db: str = fastapi.Depends(get_db),
        auth: str = fastapi.Depends(verify_auth),
    ):
        return {
            "users": ["Alice"],
            "db": db,
            "auth": auth,
            "query": q,
            "session": request.state.session_id,
        }

    app.include_pipeline(pipeline, prefix="/api")

    result = await app.exec(
        "/api/users",
        query_params={"q": "search_term"},
        state={"session_id": "sess-001"},
    )

    assert result["users"] == ["Alice"]
    assert result["db"] == "db:sqlite:///prod.db"
    assert result["auth"] == "auth:s3cret"
    assert result["query"] == "search_term"
    assert result["session"] == "sess-001"

    # Dependencies cached within the single exec
    assert call_counts["config"] == 1
    assert call_counts["auth"] == 1
