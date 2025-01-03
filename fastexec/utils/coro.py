import inspect

from starlette.concurrency import run_in_threadpool


def is_coroutine_callable(callable_obj):
    return inspect.iscoroutinefunction(callable_obj)


async def call_any_function(func, **kwargs):
    if is_coroutine_callable(func):
        # Async function, just await it
        return await func(**kwargs)
    else:
        # Sync function, run in threadpool
        return await run_in_threadpool(func, **kwargs)
