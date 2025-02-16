# fastexec

**Version:** 0.4.0
**License:** [MIT](LICENSE)

Execute functions with FastAPI features—dependency injection, request/response objects, and more—without running a full server.

## Summary

**fastexec** allows you to invoke a function as if it were a FastAPI endpoint, leveraging FastAPI's dependency-injection system. This is particularly useful for:

- **Testing** and **debugging** routes and dependencies without spinning up the entire application.
- **Dry-running** code that ordinarily depends on HTTP request and response objects.
- **Refactoring** or **benchmarking** your API logic in isolation.

Under the hood, **fastexec** uses a lightweight, mocked request context that simulates FastAPI's environment so your dependencies “just work.”

## Installation

Requires **Python 3.12+**.

```bash
pip install fastexec
```

## Quick Start

1. **Install and Import** fastexec.

2. **Create your normal FastAPI dependencies** and endpoints:

   ```python
   import fastapi
   from fastexec import FastExec

   def my_dependency(request: fastapi.Request):
       return request.headers.get("Authorization")

   async def my_endpoint(auth: str = fastapi.Depends(my_dependency)):
       return {"auth": auth}
   ```

3. **Wrap your endpoint with** `FastExec`:

   ```python
   import asyncio

   async def main():
       app = FastExec(call=my_endpoint)
       result = await app.exec(
           headers={"Authorization": "Bearer your_token_here"},
       )
       print(result)  # {'auth': 'Bearer your_token_here'}

   asyncio.run(main())
   ```

## Usage

### 1. Define Your Dependencies and Endpoint

Just like any FastAPI route, define your standard dependencies:

```python
def get_api_key(request: fastapi.Request):
    return request.headers.get("Authorization")

def process_data(api_key: str = fastapi.Depends(get_api_key)):
    # Implement your core logic
    return {"authorized": bool(api_key), "api_key": api_key}
```

### 2. Create a `FastExec` Instance

```python
from fastexec import FastExec

executor = FastExec(call=process_data)
```

The `call` parameter is the **function** or **async function** you want to invoke with dependency injection.

### 3. Execute the Function

Use the `.exec()` method to supply query parameters, headers, request body, or custom state:

```python
import asyncio

async def run_logic():
    result = await executor.exec(
        query_params={"sort": "desc"},
        headers={"Authorization": "Bearer example-token"},
        body={"example": "payload"},
        state={"session_id": "test_session_123"},
    )
    print(result)

asyncio.run(run_logic())
```

**Arguments**:

- **`query_params`**: A dictionary-like object, converted into a `?key=value` style query string for your dependencies.
- **`headers`**: A dictionary-like object representing HTTP headers (e.g., `"Authorization": "Bearer ..."`).
- **`body`**: JSON-serializable object or raw bytes. If it’s a dictionary or Pydantic model, it will be parsed as JSON and passed to body/`request.json()`.
- **`state`**: A dictionary for per-request data stored on `request.state`.
- **`state=...`** on the `FastExec(...)` constructor sets up `app.state` globally for your function calls.

## Advanced Usage

### Directly Calling Dependencies

If you want full control, you can manually create a FastAPI “dependant” object and invoke it with `exec_with_dependant`:

```python
from fastexec import get_dependant, exec_with_dependant

def core_logic(data: dict = fastapi.Body(...)):
    return {"processed": True, "data": data}

dependant = get_dependant(call=core_logic)

result = await exec_with_dependant(
    dependant=dependant,
    body={"hello": "world"},
    headers={"x-api-key": "12345"},
)
print(result)  # {"processed": True, "data": {"hello": "world"}}
```

This API is handy for low-level testing or custom injection beyond the `FastExec` class.

### Passing Application State

You can store application-wide data in `FastExec(..., state=...)`, which is then accessible via `request.app.state` in your dependencies. For example:

```python
def read_app_name(request: fastapi.Request):
    return request.app.state.app_name  # app_name is set in `state=...` dict

async def example_endpoint(app_name: str = fastapi.Depends(read_app_name)):
    return {"app_name": app_name}

# Setting a global app state
app_exec = FastExec(call=example_endpoint, state={"app_name": "Test App"})

result = await app_exec.exec()
# result == {"app_name": "Test App"}
```

### Including `request.state`

When you call `.exec()`, you can also attach **per-request** state. This becomes available as `request.state`:

```python
result = await app_exec.exec(
    state={"session_id": "session_001"},
)
# Access `request.state.session_id` inside your dependencies
```

## Examples

> See the [tests](./tests/) folder for full examples of how to wire up multiple dependencies, mock request bodies, pass custom state, handle async routes, and more.

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
5. **Open** a Pull Request. :rocket:

## License

**fastexec** is distributed under the terms of the [MIT License](./LICENSE).
