"""
Phase 7: FastAPI Response & Exception Compatibility
Dependencies: Phase 1, Phase 5

Tests that fastexec produces responses consistent with FastAPI behavior:
- Response models, status codes
- FastAPI exceptions (HTTPException, RequestValidationError)
- JSONResponse, Response objects
"""

import fastapi
import fastapi.exceptions
import fastapi.responses
import pydantic
import pytest

from fastexec import FastExec, Pipeline


# --- 7.1 Response model ---


class UserOut(pydantic.BaseModel):
    id: int
    name: str


@pytest.mark.asyncio
async def test_response_model():
    """Endpoint can declare a response_model, output is serialized accordingly."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_user():
        return {"id": 1, "name": "Alice", "secret": "should_be_stripped"}

    pipeline.register("/user", get_user, response_model=UserOut)
    app.include_pipeline(pipeline)

    result = await app.exec("/user")
    assert result == {"id": 1, "name": "Alice"}
    assert "secret" not in result


# --- 7.2 Status code in response ---


@pytest.mark.asyncio
async def test_status_code_default():
    """Default status code is 200."""
    app = FastExec()
    pipeline = Pipeline()

    async def handler():
        return {"ok": True}

    pipeline.register("/ok", handler)
    app.include_pipeline(pipeline)

    response = await app.exec("/ok")
    assert response == {"ok": True}


@pytest.mark.asyncio
async def test_status_code_custom():
    """Endpoint can declare a custom status_code."""
    app = FastExec()
    pipeline = Pipeline()

    async def create_item():
        return {"id": 1, "name": "Widget"}

    pipeline.register("/items", create_item, status_code=201)
    app.include_pipeline(pipeline)

    response = await app.exec("/items")
    assert response == {"id": 1, "name": "Widget"}


# --- 7.3 HTTPException ---


@pytest.mark.asyncio
async def test_http_exception_404():
    """HTTPException raised in endpoint propagates with correct status."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_user():
        raise fastapi.HTTPException(status_code=404, detail="User not found")

    pipeline.register("/user", get_user)
    app.include_pipeline(pipeline)

    with pytest.raises(fastapi.HTTPException) as exc_info:
        await app.exec("/user")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_http_exception_403():
    """HTTPException with 403 Forbidden."""
    app = FastExec()
    pipeline = Pipeline()

    async def admin_only():
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    pipeline.register("/admin", admin_only)
    app.include_pipeline(pipeline)

    with pytest.raises(fastapi.HTTPException) as exc_info:
        await app.exec("/admin")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_http_exception_in_dependency():
    """HTTPException raised in a dependency propagates correctly."""
    app = FastExec()
    pipeline = Pipeline()

    def verify_token(authorization: str = fastapi.Header()):
        if authorization != "Bearer valid":
            raise fastapi.HTTPException(status_code=401, detail="Invalid token")
        return "verified"

    async def handler(auth: str = fastapi.Depends(verify_token)):
        return {"auth": auth}

    pipeline.register("/secure", handler)
    app.include_pipeline(pipeline)

    with pytest.raises(fastapi.HTTPException) as exc_info:
        await app.exec("/secure", headers={"Authorization": "Bearer invalid"})

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


# --- 7.4 Request validation error ---


@pytest.mark.asyncio
async def test_validation_error_missing_required_query():
    """Missing required query param raises RequestValidationError."""
    app = FastExec()
    pipeline = Pipeline()

    async def search(q: str = fastapi.Query()):
        return {"q": q}

    pipeline.register("/search", search)
    app.include_pipeline(pipeline)

    with pytest.raises(fastapi.exceptions.RequestValidationError):
        await app.exec("/search")  # missing required 'q'


@pytest.mark.asyncio
async def test_validation_error_wrong_type():
    """Wrong type for query param raises RequestValidationError."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_page(page: int = fastapi.Query()):
        return {"page": page}

    pipeline.register("/page", get_page)
    app.include_pipeline(pipeline)

    with pytest.raises(fastapi.exceptions.RequestValidationError):
        await app.exec("/page", query_params={"page": "not_a_number"})


@pytest.mark.asyncio
async def test_validation_error_invalid_body():
    """Invalid body against Pydantic model raises RequestValidationError."""

    class ItemCreate(pydantic.BaseModel):
        name: str
        price: float

    app = FastExec()
    pipeline = Pipeline()

    async def create_item(item: ItemCreate):
        return {"name": item.name, "price": item.price}

    pipeline.register("/items", create_item)
    app.include_pipeline(pipeline)

    with pytest.raises(fastapi.exceptions.RequestValidationError):
        await app.exec("/items", body={"name": "Widget"})  # missing 'price'


# --- 7.5 JSONResponse / Response objects ---


@pytest.mark.asyncio
async def test_return_json_response():
    """Endpoint can return a JSONResponse directly."""
    app = FastExec()
    pipeline = Pipeline()

    async def handler():
        return fastapi.responses.JSONResponse(
            content={"msg": "created"}, status_code=201
        )

    pipeline.register("/create", handler)
    app.include_pipeline(pipeline)

    result = await app.exec("/create")
    assert isinstance(result, fastapi.responses.JSONResponse)
    assert result.status_code == 201


@pytest.mark.asyncio
async def test_return_plain_response():
    """Endpoint can return a plain Response."""
    app = FastExec()
    pipeline = Pipeline()

    async def handler():
        return fastapi.Response(content="OK", media_type="text/plain", status_code=200)

    pipeline.register("/health", handler)
    app.include_pipeline(pipeline)

    result = await app.exec("/health")
    assert isinstance(result, fastapi.Response)
    assert result.body == b"OK"


# --- 7.6 response_model + status_code combined ---


@pytest.mark.asyncio
async def test_response_model_with_status_code():
    """response_model and status_code work together."""

    class ItemOut(pydantic.BaseModel):
        id: int
        name: str

    app = FastExec()
    pipeline = Pipeline()

    async def create_item():
        return {"id": 1, "name": "Widget", "internal_note": "strip_this"}

    pipeline.register("/items", create_item, response_model=ItemOut, status_code=201)
    app.include_pipeline(pipeline)

    result = await app.exec("/items")
    assert result == {"id": 1, "name": "Widget"}
    assert "internal_note" not in result
