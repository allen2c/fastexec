# fastexec

**Version:** 0.6.0
**License:** [MIT](LICENSE)

Execute functions with FastAPI features—dependency injection, validation, response models, and more—without running a full server.

## Summary

**fastexec** lets you build and execute function pipelines using the same patterns as FastAPI: dependency injection via `Depends()`, Pydantic validation via type hints, response model filtering, and layered state management. No HTTP server required.

Use cases:

- **Offline execution** of FastAPI-style endpoints (batch jobs, scripts, CLI tools)
- **Testing** route logic and dependency chains without spinning up a server
- **Workflow orchestration** with typed, validated pipelines

## Installation

Requires **Python 3.11+**.

```bash
pip install fastexec
```

For visualization support (dependency graph rendering):

```bash
pip install fastexec[all]
```

## Quick Start

```python
import asyncio
import fastapi
from fastexec import FastExec, Pipeline

# Define a pipeline (like FastAPI's APIRouter)
pipeline = Pipeline()

@pipeline.register("/greet")
async def greet(name: str = fastapi.Query("World")):
    return {"message": f"Hello, {name}!"}

# Create the app (like FastAPI())
app = FastExec()
app.include_pipeline(pipeline)

# Execute
async def main():
    result = await app.exec("/greet", query_params={"name": "Alice"})
    print(result)  # {'message': 'Hello, Alice!'}

asyncio.run(main())
```

## Core Concepts

### FastExec (App) and Pipeline (Router)

`FastExec` is the application object (analogous to `FastAPI()`). `Pipeline` is a route group (analogous to `APIRouter`).

```python
from fastexec import FastExec, Pipeline

users = Pipeline()
orders = Pipeline()

@users.register("/list")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

@orders.register("/list")
async def list_orders():
    return [{"id": 101, "total": 42.0}]

app = FastExec()
app.include_pipeline(users, prefix="/users")
app.include_pipeline(orders, prefix="/orders")

# Dispatch by path
await app.exec("/users/list")   # -> [{"id": 1, "name": "Alice"}]
await app.exec("/orders/list")  # -> [{"id": 101, "total": 42.0}]
```

### Dependency Injection

Three layers of dependencies cascade: **app → pipeline → endpoint**. All use FastAPI's `Depends()`.

```python
import fastapi
from fastexec import FastExec, Pipeline

async def app_auth(request: fastapi.Request):
    """App-level dependency — runs for every endpoint."""
    token = request.headers.get("authorization")
    if not token:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

async def pipeline_logger():
    """Pipeline-level dependency — runs for endpoints in this pipeline."""
    print("Pipeline executing")

async def get_user_id(user_id: int = fastapi.Query(...)):
    return user_id

pipeline = Pipeline(dependencies=[fastapi.Depends(pipeline_logger)])

@pipeline.register("/profile")
async def profile(uid: int = fastapi.Depends(get_user_id)):
    return {"user_id": uid}

app = FastExec(dependencies=[fastapi.Depends(app_auth)])
app.include_pipeline(pipeline, prefix="/users")

result = await app.exec(
    "/users/profile",
    query_params={"user_id": 42},
    headers={"authorization": "Bearer token"},
)
# result == {"user_id": 42}
```

### State Management

App-level state is set via `FastExec(state=...)` and accessed through `request.app.state`. Per-request state is passed via `exec(state=...)` and accessed through `request.state`.

```python
app = FastExec(state={"db_url": "postgres://localhost/mydb"})

pipeline = Pipeline()

@pipeline.register("/info")
async def info(request: fastapi.Request):
    return {
        "db": request.app.state.db_url,
        "session": request.state.session_id,
    }

app.include_pipeline(pipeline)

result = await app.exec("/info", state={"session_id": "abc123"})
# result == {"db": "postgres://localhost/mydb", "session": "abc123"}
```

### Auto Validation via Type Hints

Like FastAPI, type annotations drive runtime validation. Pydantic models as parameter types auto-parse the request body; return type annotations auto-filter the response.

```python
import pydantic

class UserCreate(pydantic.BaseModel):
    name: str
    email: str

class UserResponse(pydantic.BaseModel):
    name: str
    email: str

pipeline = Pipeline()

@pipeline.register("/create")
async def create_user(user: UserCreate) -> UserResponse:
    # Return extra fields — they'll be stripped by the return type
    return {"name": user.name, "email": user.email, "internal_id": 999}

app = FastExec()
app.include_pipeline(pipeline, prefix="/users")

result = await app.exec("/users/create", body={"name": "Alice", "email": "alice@example.com"})
# result == {"name": "Alice", "email": "alice@example.com"}
# "internal_id" is filtered out by the UserResponse return type
```

### Response Model and Status Code

Explicit `response_model` and `status_code` can be set on `register()`:

```python
pipeline.register("/create", create_user, response_model=UserResponse, status_code=201)
```

### Nested Pipelines

Pipelines can include other pipelines, just like FastAPI's nested routers:

```python
child = Pipeline()

@child.register("/detail")
async def detail():
    return {"detail": "nested"}

parent = Pipeline()
parent.include_pipeline(child, prefix="/child")

app = FastExec()
app.include_pipeline(parent, prefix="/parent")

await app.exec("/parent/child/detail")  # -> {"detail": "nested"}
```

## Dependency Visualization

Understand your dependency tree with built-in visualization:

```bash
pip install fastexec[all]
```

```python
from fastexec import get_dependant
from fastexec.utils.graph import visualize_dependant, save_dependant_graph_image

dependant = get_dependant(call=my_endpoint)
save_dependant_graph_image(dependant, "deps.png", name="My Dependencies")
```

## Examples

See the [tests/](./tests/) folder for comprehensive examples covering all features.

## Contributing

1. **Fork** this repo.
2. **Create** a feature branch and make changes.
3. **Install** dev requirements:
   ```bash
   poetry install -E all --with dev
   ```
4. **Run Tests**:
   ```bash
   make pytest
   ```
5. **Open** a Pull Request.

## License

**fastexec** is distributed under the terms of the [MIT License](./LICENSE).
