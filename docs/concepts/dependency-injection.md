# Dependency Injection

fastexec reuses FastAPI's dependency injection engine directly. If you know `Depends()` in FastAPI, it works identically here.

## Three Layers

Dependencies cascade from app → pipeline → endpoint. All three layers run for each `exec()` call.

```plaintext
app.exec("/path")
  └── app dependencies        (e.g., auth check)
      └── pipeline dependencies  (e.g., logging)
          └── endpoint dependencies  (e.g., get current user)
              └── endpoint function
```

```python
import fastapi
from fastexec import FastExec, Pipeline

async def app_dep():
    print("app dep")

async def pipeline_dep():
    print("pipeline dep")

async def endpoint_dep():
    return "dep_value"

pipeline = Pipeline(dependencies=[fastapi.Depends(pipeline_dep)])

@pipeline.register("/example")
async def example(value: str = fastapi.Depends(endpoint_dep)):
    return {"value": value}

app = FastExec(dependencies=[fastapi.Depends(app_dep)])
app.include_pipeline(pipeline)

await app.exec("/example")
# prints: "app dep", "pipeline dep"
# returns: {"value": "dep_value"}
```

## Request-Scope Caching

Within a single `exec()` call, each dependency function is called at most once. Repeated use of the same dependency returns the cached result.

```python
call_count = 0

def counted_dep():
    global call_count
    call_count += 1
    return call_count

async def handler(
    a: int = fastapi.Depends(counted_dep),
    b: int = fastapi.Depends(counted_dep),  # same dep — reuses cached result
):
    return {"a": a, "b": b}

# a == b == 1, call_count == 1
```

Caching is scoped to the request — the next `exec()` call starts fresh.

## Compilation Caching

The first time you `exec()` a path, fastexec compiles that route's dependency graph (the merged app → pipeline → endpoint `Depends()` tree) and its response-model adapter, then reuses them on every later call to the same path. Running `exec()` in a loop does not rebuild them.

This caches the *structure*, not the *values* — your dependency functions still run on every call (the request-scope caching above is per-`exec()`, unchanged). Only the wiring is reused.

Because compilation is frozen after the first call to a path, register all routes and set app/pipeline dependencies **before** the first `exec()`.

## Accessing State in Dependencies

Dependencies receive the full `Request` object, so they can read app state and request state:

```python
def get_db(request: fastapi.Request):
    return request.app.state.db_url

def get_session(request: fastapi.Request):
    return request.state.session_id

@pipeline.register("/info")
async def info(
    db: str = fastapi.Depends(get_db),
    session: str = fastapi.Depends(get_session),
):
    return {"db": db, "session": session}
```

## Dependency Chains

Dependencies can depend on other dependencies:

```python
def get_token(request: fastapi.Request):
    return request.headers.get("authorization", "").removeprefix("Bearer ")

def get_user(token: str = fastapi.Depends(get_token)):
    return {"user": f"user_for_{token}"}

@pipeline.register("/profile")
async def profile(user: dict = fastapi.Depends(get_user)):
    return user
```
