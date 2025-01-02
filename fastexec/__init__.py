import asyncio
import inspect
import json
import typing
from contextlib import AsyncExitStack
from urllib.parse import urlencode

import fastapi
import fastapi.dependencies.models
import fastapi.dependencies.utils
import fastapi.exceptions
import pydantic
import starlette.requests
from starlette.concurrency import run_in_threadpool

from fastexec.version import get_version

T = typing.TypeVar("T")
__version__ = get_version()


def is_coroutine_callable(callable_obj):
    return inspect.iscoroutinefunction(callable_obj)


async def call_any_function(func, **kwargs):
    if is_coroutine_callable(func):
        # Async function, just await it
        return await func(**kwargs)
    else:
        # Sync function, run in threadpool
        return await run_in_threadpool(func, **kwargs)


def dict_to_asgi_headers(
    headers: typing.Mapping[typing.Text, typing.Text]
) -> typing.List[typing.Tuple[bytes, bytes]]:
    return [
        (k.lower().encode("latin1"), v.encode("latin1")) for k, v in headers.items()
    ]


def get_dependant(
    *, path: typing.Text = "/", call: typing.Callable
) -> fastapi.dependencies.models.Dependant:
    return fastapi.dependencies.utils.get_dependant(path=path, call=call)


async def exec_with_dependant(
    *,
    dependant: fastapi.dependencies.models.Dependant,
    query_params: typing.Optional[typing.Union[typing.Dict, pydantic.BaseModel]] = None,
    headers: typing.Optional[
        typing.Union[typing.Mapping[typing.Text, typing.Text], pydantic.BaseModel]
    ] = None,
    body: typing.Optional[typing.Union[typing.Any, pydantic.BaseModel]] = None,
) -> typing.Any:

    _query_params: typing.Dict = (
        json.loads(query_params.model_dump_json())
        if isinstance(query_params, pydantic.BaseModel)
        else query_params
    ) or {}
    _headers: typing.Mapping[typing.Text, typing.Text] = (
        json.loads(headers.model_dump_json())
        if isinstance(headers, pydantic.BaseModel)
        else headers
    ) or {}
    _body = (
        json.loads(body.model_dump_json())
        if isinstance(body, pydantic.BaseModel)
        else body
    ) or None
    _body_bytes = json.dumps(_body).encode("utf-8") if _body else b""

    request = starlette.requests.Request(
        scope={
            "type": "http",
            "method": "POST",
            "path": "/fastexec",
            "query_string": urlencode(_query_params).encode("utf-8"),
            "headers": dict_to_asgi_headers(_headers),
            "client": ("127.0.0.1", 8000),
            "content-length": str(len(_body_bytes)).encode("utf-8"),
        },
        receive=lambda: asyncio.Future(),
    )

    # Mock the receive function to return the body
    async def mock_receive():
        return {"type": "http.request", "body": _body_bytes, "more_body": False}

    request._receive = mock_receive

    async with AsyncExitStack() as stack:
        solved = await fastapi.dependencies.utils.solve_dependencies(
            request=request,
            dependant=dependant,
            body=_body if isinstance(_body, typing.Dict) else None,
            async_exit_stack=stack,  # Required
            embed_body_fields=(
                False if isinstance(_body, typing.Dict) else True
            ),  # Required (usually False for non-JSON bodies)
        )

    # If there were no errors, get the final function’s return by calling the function
    # with the solved dependency values:
    if solved.errors:
        raise fastapi.exceptions.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=str(solved.errors)
        )

    # For async functions:
    final_result = await call_any_function(dependant.call, **solved.values)
    return final_result


class FastExec(typing.Generic[T]):
    def __init__(
        self,
        call: typing.Union[
            typing.Callable[..., T],
            typing.Callable[..., typing.Awaitable[T]],
        ],
        *args,
        **kwargs,
    ):
        self.dependant = get_dependant(call=call)

    async def exec(
        self,
        *,
        query_params: typing.Optional[
            typing.Union[typing.Dict, pydantic.BaseModel]
        ] = None,
        headers: typing.Optional[
            typing.Union[typing.Mapping[typing.Text, typing.Text], pydantic.BaseModel]
        ] = None,
        body: typing.Optional[typing.Union[typing.Any, pydantic.BaseModel]] = None,
        **kwargs,
    ) -> T:
        return await exec_with_dependant(
            dependant=self.dependant,
            query_params=query_params,
            headers=headers,
            body=body,
            **kwargs,
        )
