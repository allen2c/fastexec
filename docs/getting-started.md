# Getting Started

## Requirements

- Python 3.11+
- FastAPI is installed as a dependency (no need to install separately)

## Installation

```bash
pip install fastexec
```

## Your First Workflow

```python
import asyncio
import fastapi
from fastexec import FastExec

app = FastExec()

# A node graph: greet takes the `name` query input.
@app.route("/hello")
async def hello(name: str = fastapi.Query("World")):
    return {"message": f"Hello, {name}!"}

async def main():
    result = await app.exec("/hello", query_params={"name": "Alice"})
    print(result)  # {'message': 'Hello, Alice!'}

asyncio.run(main())
```

## Key Patterns

### Grouping with a Router (prefixes)

```python
from fastexec import FastExec, Router

users = Router()
orders = Router()

@users.route("/list")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

@orders.route("/list")
async def list_orders():
    return [{"id": 101, "total": 42.0}]

app = FastExec()
app.include_router(users, prefix="/users")
app.include_router(orders, prefix="/orders")

await app.exec("/users/list")   # [{"id": 1, "name": "Alice"}]
await app.exec("/orders/list")  # [{"id": 101, "total": 42.0}]
```

### Sync Functions

Both sync and async nodes work transparently:

```python
@app.route("/sync")
def sync_endpoint():
    return {"mode": "sync"}

result = await app.exec("/sync")  # works fine
```

### Error Handling

`app.exec()` raises a `LookupError` for unregistered paths:

```python
with pytest.raises(LookupError):
    await app.exec("/nonexistent")
```

FastAPI exceptions pass through as-is:

```python
@app.route("/secure")
async def secure():
    raise fastapi.HTTPException(status_code=401, detail="Unauthorized")
```

## Next Steps

- [App & Router](concepts/app-router.md)
- [Dependency Injection](concepts/dependency-injection.md)
- [State Management](concepts/state.md)
- [Validation](concepts/validation.md)
