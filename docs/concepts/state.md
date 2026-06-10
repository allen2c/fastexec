# State Management

fastexec uses FastAPI/Starlette state directly. There are two levels.

## App State

Set on the native `app.state`. Accessible in any workflow node via `request.app.state`.

```python
app = FastExec()
app.state.db_url = "postgres://localhost/mydb"
app.state.env = "production"

@app.route("/info")
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

@app.route("/me")
async def me(request: fastapi.Request):
    return {"user_id": request.state.user_id}
```

Request state is isolated — each `exec()` call gets its own state. State from one call does not leak into another.

## Both Together

App state and request state coexist on the same `Request`:

```python
app = FastExec()
app.state.db = "postgres://localhost"

@app.route("/context")
async def context(request: fastapi.Request):
    return {
        "db": request.app.state.db,            # app state
        "session": request.state.session_id,   # request state
    }

result = await app.exec("/context", state={"session_id": "xyz"})
# {"db": "postgres://localhost", "session": "xyz"}
```

## State in Dependencies

Nodes (dependencies) have the same access to state as the terminal node:

```python
def require_auth(request: fastapi.Request):
    secret = request.app.state.secret_key
    session = request.state.session_id
    if not session:
        raise fastapi.HTTPException(status_code=401)
    return f"authenticated_{session}"
```
