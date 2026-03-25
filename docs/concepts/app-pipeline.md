# App & Pipeline

## FastExec ↔ FastAPI

| fastexec                           | FastAPI equivalent                  |
|------------------------------------|-------------------------------------|
| `FastExec()`                       | `FastAPI()`                         |
| `Pipeline()`                       | `APIRouter()`                       |
| `pipeline.register("/path", fn)`   | `router.add_api_route("/path", fn)` |
| `app.include_pipeline(p, prefix=)` | `app.include_router(r, prefix=)`    |
| `await app.exec("/path", ...)`     | HTTP request to the server          |

## FastExec

`FastExec` is the central application object. It holds app-level state and dependencies, and owns the routing table.

```python
from fastexec import FastExec

app = FastExec(
    state={"db_url": "postgres://localhost/mydb"},
    dependencies=[fastapi.Depends(require_auth)],
)
```

**Parameters:**

- `state` — a `dict` of key-value pairs accessible via `request.app.state`
- `dependencies` — app-level `Depends()` that run for every endpoint

## Pipeline

`Pipeline` groups related endpoints. It can have its own dependencies that apply to all its endpoints.

```python
from fastexec import Pipeline

pipeline = Pipeline(
    dependencies=[fastapi.Depends(require_admin)],
)
```

### Registration

Both styles are supported:

```python
# Explicit
pipeline.register("/users", get_users)

# Decorator
@pipeline.register("/users")
async def get_users():
    return [...]
```

Optional registration parameters:

```python
pipeline.register(
    "/users",
    create_user,
    response_model=UserResponse,
    status_code=201,
)
```

## Including Pipelines

```python
app.include_pipeline(pipeline)                    # no prefix
app.include_pipeline(pipeline, prefix="/api/v1")  # with prefix
```

## Nested Pipelines

Pipelines can include other pipelines, mirroring FastAPI's nested routers:

```python
child = Pipeline()

@child.register("/detail")
async def detail():
    return {"detail": "nested"}

parent = Pipeline()
parent.include_pipeline(child, prefix="/child")

app = FastExec()
app.include_pipeline(parent, prefix="/parent")

await app.exec("/parent/child/detail")  # {"detail": "nested"}
```

## Dispatch: app.exec()

```python
result = await app.exec(
    "/path",
    query_params={"key": "value"},   # dict, BaseModel, str, or bytes
    headers={"authorization": "..."},
    body={"field": "value"},
    state={"session_id": "abc"},     # per-request state
)
```
