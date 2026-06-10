# Dependency Injection

fastexec *is* FastAPI's dependency injection — the dependency graph is your workflow DAG. If you know `Depends()`, you already know how to build workflows here.

## Three Layers

Dependencies cascade from app → router → endpoint. All run before the terminal node, on every `exec()`.

```plaintext
app.exec("/path")
  ├── app dependencies       (FastExec(dependencies=[...]))
  ├── router dependencies    (Router(dependencies=[...]))
  ├── endpoint dependencies  (Depends(...) on the route function)
  └── the route function (the terminal node)
```

```python
import fastapi
from fastexec import FastExec, Router

async def app_dep():
    print("app dep")

async def router_dep():
    print("router dep")

async def node_dep():
    return "value"

router = Router(dependencies=[fastapi.Depends(router_dep)])

@router.route("/example")
async def example(value: str = fastapi.Depends(node_dep)):
    return {"value": value}

app = FastExec(dependencies=[fastapi.Depends(app_dep)])
app.include_router(router)

await app.exec("/example")
# prints: "app dep", "router dep"
# returns: {"value": "value"}
```

## Request-Scope Caching (memoization)

Within a single `exec()`, each dependency runs at most once; repeated use of the same dependency reuses the cached result. This is what makes a shared node in the DAG run once.

```python
call_count = 0

def counted_dep():
    global call_count
    call_count += 1
    return call_count

async def handler(
    a: int = fastapi.Depends(counted_dep),
    b: int = fastapi.Depends(counted_dep),  # same node — reuses the cached result
):
    return {"a": a, "b": b}

# a == b == 1, call_count == 1
```

The cache is scoped to the run — the next `exec()` starts fresh. Opt a node out with `Depends(fn, use_cache=False)`.

## Accessing State in Nodes

Nodes receive the full `Request`, so they can read app and request state:

```python
def get_db(request: fastapi.Request):
    return request.app.state.db_url

def get_session(request: fastapi.Request):
    return request.state.session_id

@app.route("/info")
async def info(
    db: str = fastapi.Depends(get_db),
    session: str = fastapi.Depends(get_session),
):
    return {"db": db, "session": session}
```

## Dependency Chains

Nodes can depend on other nodes:

```python
def get_token(request: fastapi.Request):
    return request.headers.get("authorization", "").removeprefix("Bearer ")

def get_user(token: str = fastapi.Depends(get_token)):
    return {"user": f"user_for_{token}"}

@app.route("/profile")
async def profile(user: dict = fastapi.Depends(get_user)):
    return user
```
