# fastexec

**Version:** 0.7.0
**License:** [MIT](LICENSE)

Define a workflow as a typed dependency graph and run it serverlessly — no HTTP server.

## Summary

fastexec is a **serverless workflow engine** whose DAG executor *is* FastAPI's dependency injection. A `Depends()` is a node's input edge, a function's return is its output, the dependency graph is the workflow DAG, and resolution order is execution order — with shared nodes memoized. You define workflows with the FastAPI patterns you already know, and run them in-process with `exec()`.

| Workflow concept | FastAPI mechanism |
|---|---|
| task / node | a function (dependency callable) |
| node input | `param = Depends(upstream)` |
| node output | the return value |
| the DAG | the dependency graph |
| run a workflow | `exec(path, inputs...)` |

fastexec subclasses FastAPI, so behaviour is **100% FastAPI** — no new execution semantics.

## Installation

Requires **Python 3.11+**.

```bash
pip install fastexec
```

## Quick Start

```python
import asyncio
import fastapi
from fastexec import FastExec

app = FastExec()

@app.route("/greet")
async def greet(name: str = fastapi.Query("World")):
    return {"message": f"Hello, {name}!"}

async def main():
    result = await app.exec("/greet", query_params={"name": "Alice"})
    print(result)  # {'message': 'Hello, Alice!'}

asyncio.run(main())
```

## Core Concepts

### A workflow is a dependency graph

Each `Depends()` is an upstream node; the function's parameters are its inputs and its return value is its output. `exec()` resolves the graph in execution order, memoizing shared nodes.

```python
def get_token(request: fastapi.Request):
    return "t"

def get_user(token: str = fastapi.Depends(get_token)):   # depends on get_token
    return f"user-{token}"

@app.route("/me")
async def me(user: str = fastapi.Depends(get_user)):     # depends on get_user
    return {"user": user}

await app.exec("/me")  # -> {"user": "user-t"}
```

### Grouping with Router

`Router` (= FastAPI's `APIRouter`) groups workflows with shared dependencies and a prefix:

```python
import fastapi
from fastexec import FastExec, Router

async def auth(request: fastapi.Request):
    if not request.headers.get("authorization"):
        raise fastapi.HTTPException(status_code=401)

users = Router(dependencies=[fastapi.Depends(auth)])

@users.route("/me")
async def me():
    return {"user": "alice"}

app = FastExec()
app.include_router(users, prefix="/users")

await app.exec("/users/me", headers={"authorization": "Bearer t"})
```

App-level dependencies (`FastExec(dependencies=[...])`) run for every workflow; router-level ones run for every workflow in that router.

### State

App state is FastAPI-native; per-`exec` state lands on `request.state`:

```python
app = FastExec()
app.state.db = "postgres://localhost/mydb"

@app.route("/info")
async def info(request: fastapi.Request):
    return {"db": request.app.state.db, "session": request.state.session_id}

await app.exec("/info", state={"session_id": "abc123"})
# -> {"db": "postgres://localhost/mydb", "session": "abc123"}
```

### Validation via type hints

Pydantic models as parameter types auto-parse the body; return-type or `response_model` filters the output.

```python
import pydantic

class UserCreate(pydantic.BaseModel):
    name: str
    email: str

class UserResponse(pydantic.BaseModel):
    name: str
    email: str

@app.route("/users/create")
async def create_user(user: UserCreate) -> UserResponse:
    return {"name": user.name, "email": user.email, "internal_id": 999}

await app.exec("/users/create", body={"name": "Alice", "email": "a@e.com"})
# -> {"name": "Alice", "email": "a@e.com"}   (internal_id stripped)
```

### Path parameters

Routes can be templated, exactly as in FastAPI:

```python
@app.route("/items/{item_id}")
async def get_item(item_id: int):
    return {"id": item_id}

await app.exec("/items/42")  # -> {"id": 42}
```

## Examples

See the [tests/](./tests/) folder for comprehensive examples covering all features.

## Migrating from 0.6

v0.7.0 is a breaking redesign — fastexec now subclasses FastAPI:

- **`Pipeline` is gone.** Register workflows directly on the app with `@app.route(...)`. For grouping / shared dependencies / prefix, use `Router` (= `APIRouter`) + `app.include_router(router, prefix=...)`.
- **`@pipeline.register(...)` → `@app.route(...)` / `@router.route(...)`.**
- **`FastExec(state={...})` → native `app.state`** (`app.state.db = ...`; read via `request.app.state.db`).
- **`get_dependant`** is gone from the public API — import FastAPI's directly if needed.

## Contributing

1. **Fork** this repo.
2. **Create** a feature branch and make changes.
3. **Install** dev requirements:
   ```bash
   make install
   ```
4. **Run Tests**:
   ```bash
   make pytest
   ```
5. **Open** a Pull Request.

## License

**fastexec** is distributed under the terms of the [MIT License](./LICENSE).
