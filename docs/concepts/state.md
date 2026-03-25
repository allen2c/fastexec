# State Management

fastexec supports two levels of state, mirroring how FastAPI and Starlette handle state.

## App State

Set once at `FastExec` creation. Accessible in any endpoint or dependency via `request.app.state`.

```python
app = FastExec(state={"db_url": "postgres://localhost/mydb", "env": "production"})

@pipeline.register("/info")
async def info(request: fastapi.Request):
    return {
        "db": request.app.state.db_url,
        "env": request.app.state.env,
    }
```

App state is shared across all `exec()` calls for the lifetime of the `FastExec` instance.

## Request State

Passed per `exec()` call via the `state=` parameter. Accessible via `request.state`.

```python
result = await app.exec("/info", state={"session_id": "abc-123", "user_id": 42})

@pipeline.register("/me")
async def me(request: fastapi.Request):
    return {"user_id": request.state.user_id}
```

Request state is isolated — each `exec()` call gets its own state object. State from one call does not leak into another.

## Both Together

App state and request state coexist on the same `Request` object:

```python
app = FastExec(state={"db": "postgres://localhost"})

@pipeline.register("/context")
async def context(request: fastapi.Request):
    return {
        "db": request.app.state.db,          # app state
        "session": request.state.session_id,  # request state
    }

result = await app.exec("/context", state={"session_id": "xyz"})
# {"db": "postgres://localhost", "session": "xyz"}
```

## State in Dependencies

Dependencies have the same access to state as endpoints:

```python
def require_auth(request: fastapi.Request):
    secret = request.app.state.secret_key
    session = request.state.session_id
    if not session:
        raise fastapi.HTTPException(status_code=401)
    return f"authenticated_{session}"
```
