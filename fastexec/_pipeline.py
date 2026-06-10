import typing


class RouteConfig(typing.NamedTuple):
    endpoint: typing.Callable
    response_model: typing.Optional[typing.Any] = None


class Pipeline:
    def __init__(
        self,
        *,
        dependencies: typing.Optional[typing.List] = None,
    ):
        self.dependencies = list(dependencies or [])
        self._routes: typing.Dict[str, RouteConfig] = {}

    def register(
        self,
        path: str,
        endpoint: typing.Optional[typing.Callable] = None,
        *,
        response_model: typing.Optional[typing.Any] = None,
    ):
        if endpoint is not None:
            self._routes[path] = RouteConfig(
                endpoint=endpoint,
                response_model=response_model,
            )
            return endpoint

        # Decorator usage: @pipeline.register("/path")
        def decorator(func: typing.Callable) -> typing.Callable:
            self._routes[path] = RouteConfig(
                endpoint=func,
                response_model=response_model,
            )
            return func

        return decorator

    def include_pipeline(
        self,
        pipeline: "Pipeline",
        *,
        prefix: str = "",
    ) -> None:
        for path, route_config in pipeline._routes.items():
            full_path = prefix + path
            self._routes[full_path] = route_config
