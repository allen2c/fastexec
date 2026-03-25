"""
Validation: response models, status codes, exceptions, and auto validation via type hints.
"""

import typing

import fastapi
import fastapi.exceptions
import fastapi.responses
import pydantic
import pytest

from fastexec import FastExec, Pipeline

# ============================================================
# Response model
# ============================================================


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


# ============================================================
# Status code
# ============================================================


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


# ============================================================
# HTTPException
# ============================================================


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


# ============================================================
# Request validation error
# ============================================================


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


# ============================================================
# JSONResponse / Response objects
# ============================================================


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


# ============================================================
# Auto validation via type hints
# ============================================================


class CreateUserRequest(pydantic.BaseModel):
    name: str
    email: str
    age: int


@pytest.mark.asyncio
async def test_auto_parse_body_from_type_hint():
    """Pydantic model type hint on param auto-parses body without Body()."""
    app = FastExec()
    pipeline = Pipeline()

    async def create_user(user: CreateUserRequest):
        return {"name": user.name, "email": user.email, "age": user.age}

    pipeline.register("/users", create_user)
    app.include_pipeline(pipeline)

    result = await app.exec(
        "/users", body={"name": "Alice", "email": "alice@test.com", "age": 30}
    )
    assert result == {"name": "Alice", "email": "alice@test.com", "age": 30}


@pytest.mark.asyncio
async def test_auto_parse_body_validation_error():
    """Invalid body against type-hinted model raises validation error."""
    app = FastExec()
    pipeline = Pipeline()

    async def create_user(user: CreateUserRequest):
        return {"name": user.name}

    pipeline.register("/users", create_user)
    app.include_pipeline(pipeline)

    with pytest.raises(fastapi.exceptions.RequestValidationError):
        await app.exec("/users", body={"name": "Alice"})  # missing email, age


@pytest.mark.asyncio
async def test_auto_parse_body_type_coercion():
    """Type coercion works: string '25' → int 25 for age field."""
    app = FastExec()
    pipeline = Pipeline()

    async def create_user(user: CreateUserRequest):
        return {"age": user.age, "age_type": type(user.age).__name__}

    pipeline.register("/users", create_user)
    app.include_pipeline(pipeline)

    result = await app.exec(
        "/users", body={"name": "Alice", "email": "a@b.com", "age": "25"}
    )
    assert result["age"] == 25
    assert result["age_type"] == "int"


class UserResponse(pydantic.BaseModel):
    id: int
    name: str


@pytest.mark.asyncio
async def test_auto_response_model_from_return_type():
    """Return type annotation acts as response_model, filtering extra fields."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_user() -> UserResponse:
        return {"id": 1, "name": "Alice", "secret": "should_be_stripped"}

    pipeline.register("/user", get_user)
    app.include_pipeline(pipeline)

    result = await app.exec("/user")
    assert result == {"id": 1, "name": "Alice"}
    assert "secret" not in result


@pytest.mark.asyncio
async def test_auto_response_validation_error():
    """Return value that doesn't match return type annotation raises error."""
    app = FastExec()
    pipeline = Pipeline()

    async def get_user() -> UserResponse:
        return {"name": "Alice"}  # missing 'id'

    pipeline.register("/user", get_user)
    app.include_pipeline(pipeline)

    with pytest.raises(Exception):  # ResponseValidationError or similar
        await app.exec("/user")


# ============================================================
# Nested models
# ============================================================


class Address(pydantic.BaseModel):
    street: str
    city: str
    zip_code: str


class UserWithAddress(pydantic.BaseModel):
    name: str
    address: Address


@pytest.mark.asyncio
async def test_nested_model_auto_parse():
    """Nested Pydantic models are auto-parsed from body."""
    app = FastExec()
    pipeline = Pipeline()

    async def create_user(user: UserWithAddress):
        return {"name": user.name, "city": user.address.city}

    pipeline.register("/users", create_user)
    app.include_pipeline(pipeline)

    result = await app.exec(
        "/users",
        body={
            "name": "Alice",
            "address": {"street": "123 Main St", "city": "Taipei", "zip_code": "100"},
        },
    )
    assert result == {"name": "Alice", "city": "Taipei"}


@pytest.mark.asyncio
async def test_nested_model_validation_error():
    """Invalid nested model raises validation error."""
    app = FastExec()
    pipeline = Pipeline()

    async def create_user(user: UserWithAddress):
        return {"name": user.name}

    pipeline.register("/users", create_user)
    app.include_pipeline(pipeline)

    with pytest.raises(fastapi.exceptions.RequestValidationError):
        await app.exec(
            "/users",
            body={"name": "Alice", "address": {"street": "123 Main St"}},
            # missing city, zip_code
        )


# ============================================================
# List and Optional types
# ============================================================


class Item(pydantic.BaseModel):
    name: str
    price: float


@pytest.mark.asyncio
async def test_list_body_type():
    """List[Model] as body type hint parses a list of models."""
    app = FastExec()
    pipeline = Pipeline()

    async def create_items(items: typing.List[Item]):
        return {"count": len(items), "names": [i.name for i in items]}

    pipeline.register("/items/batch", create_items)
    app.include_pipeline(pipeline)

    result = await app.exec(
        "/items/batch",
        body=[
            {"name": "Widget", "price": 9.99},
            {"name": "Gadget", "price": 19.99},
        ],
    )
    assert result == {"count": 2, "names": ["Widget", "Gadget"]}


@pytest.mark.asyncio
async def test_optional_body_fields():
    """Optional fields in model are not required."""

    class UpdateUser(pydantic.BaseModel):
        name: typing.Optional[str] = None
        email: typing.Optional[str] = None

    app = FastExec()
    pipeline = Pipeline()

    async def update_user(user: UpdateUser):
        return {"name": user.name, "email": user.email}

    pipeline.register("/users/update", update_user)
    app.include_pipeline(pipeline)

    result = await app.exec("/users/update", body={"name": "Bob"})
    assert result == {"name": "Bob", "email": None}


@pytest.mark.asyncio
async def test_multiple_typed_body_params():
    """Multiple Pydantic model params are embedded as sub-keys in body."""

    class UserInfo(pydantic.BaseModel):
        name: str

    class ItemInfo(pydantic.BaseModel):
        title: str

    app = FastExec()
    pipeline = Pipeline()

    async def handler(user: UserInfo, item: ItemInfo):
        return {"user_name": user.name, "item_title": item.title}

    pipeline.register("/combo", handler)
    app.include_pipeline(pipeline)

    result = await app.exec(
        "/combo",
        body={"user": {"name": "Alice"}, "item": {"title": "Widget"}},
    )
    assert result == {"user_name": "Alice", "item_title": "Widget"}


@pytest.mark.asyncio
async def test_typed_body_with_depends():
    """Type-hinted body and Depends() work together in same endpoint."""

    class OrderCreate(pydantic.BaseModel):
        product: str
        quantity: int

    def get_db():
        return "db_connection"

    app = FastExec()
    pipeline = Pipeline()

    async def create_order(
        order: OrderCreate,
        db: str = fastapi.Depends(get_db),
    ):
        return {"product": order.product, "quantity": order.quantity, "db": db}

    pipeline.register("/orders", create_order)
    app.include_pipeline(pipeline)

    result = await app.exec("/orders", body={"product": "Widget", "quantity": 3})
    assert result == {"product": "Widget", "quantity": 3, "db": "db_connection"}


@pytest.mark.asyncio
async def test_return_type_list_model():
    """Return type List[Model] serializes and filters each item."""

    class ItemOut(pydantic.BaseModel):
        id: int
        name: str

    app = FastExec()
    pipeline = Pipeline()

    async def list_items() -> typing.List[ItemOut]:
        return [
            {"id": 1, "name": "A", "internal": "x"},
            {"id": 2, "name": "B", "internal": "y"},
        ]

    pipeline.register("/items", list_items)
    app.include_pipeline(pipeline)

    result = await app.exec("/items")
    assert result == [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
