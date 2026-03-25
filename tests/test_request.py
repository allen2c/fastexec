"""
Request: passing query_params, headers, and body through exec().
"""

import fastapi
import pydantic
import pytest

from fastexec import FastExec, Pipeline

# --- Query parameters ---


@pytest.mark.asyncio
async def test_query_params():
    """Query parameters are accessible in endpoints."""
    app = FastExec()
    pipeline = Pipeline()

    async def search(q: str = fastapi.Query(), page: int = fastapi.Query(default=1)):
        return {"q": q, "page": page}

    pipeline.register("/search", search)
    app.include_pipeline(pipeline)

    result = await app.exec("/search", query_params={"q": "hello", "page": 2})
    assert result == {"q": "hello", "page": 2}


# --- Headers ---


@pytest.mark.asyncio
async def test_headers():
    """Headers are accessible in endpoints."""
    app = FastExec()
    pipeline = Pipeline()

    async def check_auth(authorization: str = fastapi.Header()):
        return {"token": authorization}

    pipeline.register("/auth", check_auth)
    app.include_pipeline(pipeline)

    result = await app.exec("/auth", headers={"Authorization": "Bearer my_token"})
    assert result == {"token": "Bearer my_token"}


# --- Body ---


@pytest.mark.asyncio
async def test_body_dict():
    """Dict body is accessible in endpoints."""
    app = FastExec()
    pipeline = Pipeline()

    async def create_user(body: dict = fastapi.Body()):
        return {"created": body["name"]}

    pipeline.register("/users", create_user)
    app.include_pipeline(pipeline)

    result = await app.exec("/users", body={"name": "Alice", "email": "alice@test.com"})
    assert result == {"created": "Alice"}


@pytest.mark.asyncio
async def test_body_pydantic_model():
    """Pydantic model body is validated and accessible."""

    class UserCreate(pydantic.BaseModel):
        name: str
        email: str

    app = FastExec()
    pipeline = Pipeline()

    async def create_user(user: UserCreate):
        return {"created": user.name, "email": user.email}

    pipeline.register("/users", create_user)
    app.include_pipeline(pipeline)

    result = await app.exec("/users", body={"name": "Alice", "email": "alice@test.com"})
    assert result == {"created": "Alice", "email": "alice@test.com"}


# --- Combined params ---


@pytest.mark.asyncio
async def test_combined_query_headers_body():
    """Query params, headers, and body can all be used together."""
    app = FastExec()
    pipeline = Pipeline()

    async def handler(
        request: fastapi.Request,
        q: str = fastapi.Query(),
        x_request_id: str = fastapi.Header(),
        body: dict = fastapi.Body(),
    ):
        return {
            "q": q,
            "request_id": x_request_id,
            "body_name": body["name"],
        }

    pipeline.register("/combined", handler)
    app.include_pipeline(pipeline)

    result = await app.exec(
        "/combined",
        query_params={"q": "test"},
        headers={"X-Request-Id": "req-001"},
        body={"name": "Alice"},
    )
    assert result == {"q": "test", "request_id": "req-001", "body_name": "Alice"}
