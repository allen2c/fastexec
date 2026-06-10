class _RouteMixin:
    """Verbless route registration, shared by FastExec and Router."""

    def route(self, path, **kwargs):
        # The HTTP method is an internal detail; default to POST so workflows
        # can take a request body.
        kwargs.setdefault("methods", ["POST"])

        def decorator(func):
            self.add_api_route(path, func, **kwargs)
            return func

        return decorator
