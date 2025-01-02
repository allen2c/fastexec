import inspect
import typing

import fastapi.dependencies.models
import fastapi.dependencies.utils
from starlette.concurrency import run_in_threadpool

from fastexec.version import get_version

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
