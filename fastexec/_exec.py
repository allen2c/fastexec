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
import starlette.concurrency
import starlette.requests

import fastexec.utils.convert
from fastexec._pipeline import Pipeline


def get_dependant(
    *, path: str = "/", call: typing.Callable
) -> fastapi.dependencies.models.Dependant:
    return fastapi.dependencies.utils.get_dependant(path=path, call=call)


class _RouteInfo(typing.NamedTuple):
    endpoint: typing.Callable
    pipeline_dependencies: typing.List
    response_model: typing.Optional[typing.Any] = None


class _State:
    """Attribute-access wrapper for state dict, similar to Starlette's State."""

    def __init__(self, data: typing.Optional[typing.Dict] = None):
        if data:
            for key, value in data.items():
                setattr(self, key, value)


class FastExec:
    """v0.6.0 app object — analogous to FastAPI()."""

    def __init__(
        self,
        *,
        state: typing.Optional[typing.Dict] = None,
        dependencies: typing.Optional[typing.List] = None,
    ):
        self.state = _State(state)
        self._state_dict = state or {}
        self.dependencies = list(dependencies or [])
        self._routes: typing.Dict[str, _RouteInfo] = {}

    def include_pipeline(
        self,
        pipeline: Pipeline,
        *,
        prefix: str = "",
    ) -> None:
        for path, route_config in pipeline._routes.items():
            full_path = prefix + path
            self._routes[full_path] = _RouteInfo(
                endpoint=route_config.endpoint,
                pipeline_dependencies=list(pipeline.dependencies),
                response_model=route_config.response_model,
            )

    async def exec(
        self,
        path: str,
        *,
        state: typing.Optional[typing.Dict] = None,
        query_params: typing.Optional[typing.Dict] = None,
        headers: typing.Optional[typing.Dict] = None,
        body: typing.Optional[typing.Any] = None,
    ) -> typing.Any:
        route = self._routes.get(path)
        if route is None:
            raise LookupError(f"No endpoint registered for path: {path}")

        endpoint = route.endpoint
        dependant = get_dependant(path=path, call=endpoint)

        # Merge layered dependencies: app → pipeline → endpoint
        # App and pipeline deps are prepended as "guard" dependencies
        extra_deps = []
        for dep in self.dependencies:
            extra_deps.append(get_dependant(path=path, call=dep.dependency))
        for dep in route.pipeline_dependencies:
            extra_deps.append(get_dependant(path=path, call=dep.dependency))
        dependant.dependencies = extra_deps + dependant.dependencies

        # Build mock app with app-level state
        app_instance = fastapi.FastAPI()
        for key, value in self._state_dict.items():
            setattr(app_instance.state, key, value)

        # Determine effective response_model: explicit > return type annotation
        response_model = route.response_model
        if response_model is None:
            return_annotation = typing.get_type_hints(endpoint).get("return")
            if return_annotation is not None and return_annotation is not type(None):
                response_model = return_annotation

        # Build request
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
                    "app": app_instance,
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
                dependant=dependant,
                body=_body if _is_json_body else None,
                async_exit_stack=stack,
                embed_body_fields=False,
            )

            if solved.errors:
                raise fastapi.exceptions.RequestValidationError(solved.errors)

            if inspect.iscoroutinefunction(endpoint):
                result = await endpoint(**solved.values)
            else:
                result = await starlette.concurrency.run_in_threadpool(
                    endpoint, **solved.values
                )

        # Apply response_model filtering
        if response_model is not None and not isinstance(result, fastapi.Response):
            adapter = pydantic.TypeAdapter(response_model)
            validated = adapter.validate_python(result)
            result = adapter.dump_python(validated, mode="python")

        return result
