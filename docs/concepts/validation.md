# Validation

fastexec uses FastAPI's validation engine. Type annotations drive both input parsing and output filtering.

## Auto Body Parsing

A Pydantic model as a parameter type causes the request body to be parsed and validated automatically:

```python
import pydantic

class UserCreate(pydantic.BaseModel):
    name: str
    email: str

@app.route("/users")
async def create_user(user: UserCreate):
    return {"name": user.name, "email": user.email}

result = await app.exec("/users", body={"name": "Alice", "email": "alice@example.com"})
```

Invalid body raises `fastapi.exceptions.RequestValidationError`.

## Auto Response Filtering

A return type annotation acts as `response_model`, filtering the response automatically:

```python
class UserResponse(pydantic.BaseModel):
    name: str
    email: str

@app.route("/users")
async def create_user(user: UserCreate) -> UserResponse:
    return {"name": user.name, "email": user.email, "internal_id": 999}

# "internal_id" is stripped — result is {"name": ..., "email": ...}
```

## Explicit response_model

Set `response_model` explicitly on `@app.route(...)` to override or supplement the return type:

```python
@app.route("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    ...
```

When `response_model` is set explicitly, it takes precedence over the return type annotation.

## Generic Types

Generic return types like `list[Model]` are supported, exactly as in FastAPI:

```python
@app.route("/users")
async def list_users() -> list[UserResponse]:
    return [{"name": "Alice", "email": "alice@example.com", "internal_id": 999}]

# internal_id stripped from each item
```

## Exceptions

Use FastAPI exceptions directly — they are passed through as-is:

```python
raise fastapi.HTTPException(status_code=404, detail="Not found")
raise fastapi.HTTPException(status_code=422, detail=[{"loc": [...], "msg": "..."}])
```

## JSONResponse

Return a `fastapi.responses.JSONResponse` to control status code and headers:

```python
@app.route("/create")
async def create():
    return fastapi.responses.JSONResponse(
        content={"id": 1},
        status_code=201,
    )
```

## Optional and Nested Models

Optional fields and nested Pydantic models work as expected:

```python
class Address(pydantic.BaseModel):
    city: str

class Profile(pydantic.BaseModel):
    name: str
    address: typing.Optional[Address] = None
```
