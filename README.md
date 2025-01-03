# fastexec

Execute function with FastAPI features.

## Summary

Fastexec allows you to execute a function as if it were a FastAPI endpoint, leveraging FastAPI's dependency injection system. This is particularly useful for testing and debugging routes and dependencies.

## Quick Start

```python
import asyncio

import fastapi

from fastexec import FastExec


def my_dependency(request: fastapi.Request):
    return request.headers.get("Authorization")


async def my_endpoint(auth: str = fastapi.Depends(my_dependency)):
    return {"auth": auth}


async def main():
    app = FastExec(call=my_endpoint)
    result = await app.exec(headers={"Authorization": "Bearer your_token_here"})
    print(result)  # Output: {'auth': 'Bearer your_token_here'}


asyncio.run(main())
```

## Installation

```bash
pip install fastexec
```

## Usage

**1. Define your dependencies and endpoint function:**

```python
import fastapi
from fastexec import FastExec

# ... your dependencies and endpoint function
```

**2. Create a FastExec instance:**

```python
app = FastExec(call=your_endpoint_function)
```

**3. Execute the function:**

```python
result = await app.exec(
    query_params=your_query_params,
    headers=your_headers,
    body=your_body,
)
```
