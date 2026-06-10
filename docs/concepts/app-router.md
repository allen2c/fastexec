# App & Router

## fastexec ↔ FastAPI

| fastexec                         | FastAPI equivalent               |
|----------------------------------|----------------------------------|
| `FastExec()`                     | `FastAPI()`                      |
| `Router()`                       | `APIRouter()`                    |
| `@app.route("/path")`            | `@app.post("/path")`             |
| `app.include_router(r, prefix=)` | `app.include_router(r, prefix=)` |
| `await app.exec("/path", ...)`   | an HTTP request to the server    |

`FastExec` subclasses `FastAPI` and `Router` subclasses `APIRouter`, so everything FastAPI does — prefixes, nesting, dependencies, path params — works unchanged.

## FastExec

The app object. Register workflows directly on it with `@app.route`, and hold app-level state and dependencies.

```python
import fastapi
from fastexec import FastExec

app = FastExec(dependencies=[fastapi.Depends(require_auth)])
app.state.db_url = "postgres://localhost/mydb"

@app.route("/users")
async def get_users():
    return [...]
```

- `dependencies` — app-level `Depends()` that run for every workflow.
- `app.state` — native FastAPI/Starlette state, read via `request.app.state`.

## Router

`Router` groups workflows that share dependencies and a prefix. It is optional — use it only when you want grouping.

```python
from fastexec import Router

router = Router(dependencies=[fastapi.Depends(require_admin)])

@router.route("/users")
async def get_users():
    return [...]
```

## Including a Router

```python
app.include_router(router)                    # no prefix
app.include_router(router, prefix="/api/v1")  # with prefix
```

Routers can include other routers, mirroring FastAPI's nested routers:

```python
child = Router()

@child.route("/detail")
async def detail():
    return {"detail": "nested"}

parent = Router()
parent.include_router(child, prefix="/child")

app.include_router(parent, prefix="/parent")

await app.exec("/parent/child/detail")  # {"detail": "nested"}
```

## Running a workflow: app.exec()

```python
result = await app.exec(
    "/path",
    query_params={"key": "value"},   # dict, BaseModel, str, or bytes
    headers={"authorization": "..."},
    body={"field": "value"},
    state={"session_id": "abc"},     # per-exec request.state
)
```
