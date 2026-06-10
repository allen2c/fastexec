"""
Workflow-vocabulary aliases over the FastAPI-faithful API.
"""

import fastapi
import pytest

from fastexec import FastExec, Router, Task, Workflow


def test_workflow_is_router_alias():
    assert Workflow is Router


def test_task_is_depends_alias():
    assert Task is fastapi.Depends


def test_run_is_exec_alias():
    assert FastExec.run is FastExec.exec


@pytest.mark.asyncio
async def test_workflow_vocabulary_end_to_end():
    def load():
        return "data"

    app = FastExec()

    @app.workflow("/process")
    async def process(d: str = Task(load)):
        return {"got": d}

    assert await app.run("/process") == {"got": "data"}


@pytest.mark.asyncio
async def test_workflow_grouping_alias():
    orders = Workflow()

    @orders.workflow("/list")
    async def list_orders():
        return [1, 2]

    app = FastExec()
    app.include_router(orders, prefix="/orders")
    assert await app.run("/orders/list") == [1, 2]
