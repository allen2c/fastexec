# fastexec

**Execute functions with FastAPI features — no server required.**

[![PyPI](https://img.shields.io/pypi/v/fastexec)](https://pypi.org/project/fastexec/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/allen2c/fastexec/blob/main/LICENSE)

---

**fastexec** lets you build and execute function pipelines using the same patterns as FastAPI: dependency injection via `Depends()`, Pydantic validation via type hints, response model filtering, and layered state management.

Use cases:

- **Offline execution** of FastAPI-style endpoints (batch jobs, scripts, CLI tools)
- **Testing** route logic and dependency chains without spinning up a server
- **Workflow orchestration** with typed, validated pipelines

## Installation

```bash
pip install fastexec
```

## Quick Start

```python
import asyncio
import fastapi
from fastexec import FastExec, Pipeline

pipeline = Pipeline()

@pipeline.register("/greet")
async def greet(name: str = fastapi.Query("World")):
    return {"message": f"Hello, {name}!"}

app = FastExec()
app.include_pipeline(pipeline)

async def main():
    result = await app.exec("/greet", query_params={"name": "Alice"})
    print(result)  # {'message': 'Hello, Alice!'}

asyncio.run(main())
```

## Next Steps

- [Getting Started](getting-started.md) — installation, first pipeline, key patterns
- [Concepts](concepts/app-pipeline.md) — deep dives into each feature
- [API Reference](api-reference.md) — full API documentation
