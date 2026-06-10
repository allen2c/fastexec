import asyncio
import inspect
import json
from contextlib import AsyncExitStack
from urllib.parse import urlencode

import fastapi
import fastapi.dependencies.utils
import fastapi.exceptions
import fastapi.routing
import starlette.concurrency
import starlette.requests
import starlette.routing

import fastexec.utils.convert
from fastexec._routing import _RouteMixin


class FastExec(_RouteMixin, fastapi.FastAPI):
    """A serverless workflow app — FastAPI's dependency injection, run in-process."""

    def __init__(self, **kwargs):
        # No server -> no docs/openapi auto-routes polluting self.routes.
        kwargs.setdefault("openapi_url", None)
        super().__init__(**kwargs)

    def _match(self, path):
        scope = {"type": "http", "method": "POST", "path": path}
        for route in self.routes:
            if isinstance(route, fastapi.routing.APIRoute):
                match, child = route.matches(scope)
                if match == starlette.routing.Match.FULL:
                    return route, child.get("path_params", {})
        raise LookupError(f"No workflow registered for path: {path}")

    async def exec(
        self,
        path,
        *,
        query_params=None,
        headers=None,
        body=None,
        state=None,
    ):
        route, path_params = self._match(path)

        _query_params = fastexec.utils.convert.to_query_params(query_params)
        _headers = fastexec.utils.convert.to_headers(headers)
        if isinstance(body, list):
            _body = body
        else:
            _body = fastexec.utils.convert.to_body(body)
        _is_json_body = isinstance(_body, (dict, list))
        _body_bytes = (
            json.dumps(_body).encode("utf-8") if _is_json_body else (_body or b"")
        )

        async with AsyncExitStack() as stack:
            func_stack = AsyncExitStack()
            request = starlette.requests.Request(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": path,
                    "path_params": path_params,
                    "query_string": (
                        urlencode(_query_params).encode("utf-8")
                        if _query_params
                        else b""
                    ),
                    "headers": (
                        fastexec.utils.convert.dict_to_asgi_headers(_headers)
                        if _headers
                        else []
                    ),
                    "client": ("127.0.0.1", 8000),
                    "state": state or {},
                    "app": self,
                    "fastapi_inner_astack": stack,
                    "fastapi_function_astack": func_stack,
                },
                receive=lambda: asyncio.Future(),
            )

            async def mock_receive():
                return {
                    "type": "http.request",
                    "body": _body_bytes,
                    "more_body": False,
                }

            request._receive = mock_receive

            solved = await fastapi.dependencies.utils.solve_dependencies(
                request=request,
                dependant=route.dependant,
                body=_body if _is_json_body else None,
                async_exit_stack=stack,
                embed_body_fields=getattr(route, "_embed_body_fields", False),
            )
            if solved.errors:
                raise fastapi.exceptions.RequestValidationError(solved.errors)

            endpoint = route.endpoint
            if inspect.iscoroutinefunction(endpoint):
                result = await endpoint(**solved.values)
            else:
                result = await starlette.concurrency.run_in_threadpool(
                    endpoint, **solved.values
                )

        if route.response_field is not None and not isinstance(
            result, fastapi.Response
        ):
            result = await fastapi.routing.serialize_response(
                field=route.response_field, response_content=result
            )
        return result
