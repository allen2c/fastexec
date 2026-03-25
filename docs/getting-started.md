# Getting Started

## Requirements

- Python 3.11+
- FastAPI is installed as a dependency (no need to install separately)

## Installation

```bash
pip install fastexec
```

For dependency graph visualization support:

```bash
pip install fastexec[all]
```

## Your First Pipeline

```python
import asyncio
import fastapi
from fastexec import FastExec, Pipeline

# 1. Create a Pipeline (like APIRouter)
pipeline = Pipeline()

# 2. Register an endpoint
@pipeline.register("/hello")
async def hello(name: str = fastapi.Query("World")):
    return {"message": f"Hello, {name}!"}

# 3. Create the app and include the pipeline
app = FastExec()
app.include_pipeline(pipeline)

# 4. Execute
async def main():
    result = await app.exec("/hello", query_params={"name": "Alice"})
    print(result)  # {'message': 'Hello, Alice!'}

asyncio.run(main())
```

## Key Patterns

### Multiple Pipelines with Prefixes

```python
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

await app.exec("/users/list")   # [{"id": 1, "name": "Alice"}]
await app.exec("/orders/list")  # [{"id": 101, "total": 42.0}]
```

### Sync Functions

Both sync and async endpoint functions work transparently:

```python
@pipeline.register("/sync")
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
@pipeline.register("/secure")
async def secure():
    raise fastapi.HTTPException(status_code=401, detail="Unauthorized")
```

## Next Steps

- [App & Pipeline](concepts/app-pipeline.md)
- [Dependency Injection](concepts/dependency-injection.md)
- [State Management](concepts/state.md)
- [Validation](concepts/validation.md)
