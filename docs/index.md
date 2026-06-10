# fastexec

**Define a workflow as a typed dependency graph and run it serverlessly — no HTTP server.**

[![PyPI](https://img.shields.io/pypi/v/fastexec)](https://pypi.org/project/fastexec/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/allen2c/fastexec/blob/main/LICENSE)

---

fastexec is a serverless workflow engine whose DAG executor *is* FastAPI's dependency injection. A `Depends()` is a node's input edge, the return value is its output, the dependency graph is the workflow DAG, and resolution order is execution order — with shared nodes memoized. It subclasses FastAPI, so behaviour is 100% FastAPI.

## Installation

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

## Next Steps

- [Getting Started](getting-started.md) — installation, your first workflow, key patterns
- [Concepts](concepts/app-router.md) — deep dives into each feature
- [API Reference](api-reference.md) — full API documentation
