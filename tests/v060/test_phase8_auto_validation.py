"""
Phase 8: Auto Validation via Type Hints
Dependencies: Phase 1, Phase 5, Phase 7

Tests that fastexec automatically parses and validates input/output
based on type annotations, mirroring FastAPI's behavior:
- Function param typed as Pydantic model → body auto-parsed & validated
- Return type annotation → response auto-validated & serialized
- Nested models, Optional, List, Union — all respected
- No need for explicit Body() / response_model — typing IS the schema
"""

import typing

import fastapi
import fastapi.exceptions
import pydantic
import pytest

from fastexec import FastExec, Pipeline


# --- 8.1 Auto-parse body from type hint (no explicit Body()) ---


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


# --- 8.2 Auto-validate response from return type annotation ---


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


# --- 8.3 Nested models ---


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


# --- 8.4 List and Optional types ---


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


# --- 8.5 Multiple body params with type hints ---


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


# --- 8.6 Type hint + Depends coexistence ---


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

    result = await app.exec(
        "/orders", body={"product": "Widget", "quantity": 3}
    )
    assert result == {"product": "Widget", "quantity": 3, "db": "db_connection"}


# --- 8.7 Return type List[Model] ---


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
