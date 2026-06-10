import fastapi


class _RouteMixin:
    """Verbless route registration, shared by FastExec and Router."""

    def route(self, path, **kwargs):
        """Register a workflow at ``path``. Also available as ``workflow()``."""
        # The HTTP method is an internal detail; default to POST so workflows
        # can take a request body.
        kwargs.setdefault("methods", ["POST"])

        def decorator(func):
            self.add_api_route(path, func, **kwargs)
            return func

        return decorator

    workflow = route  # workflow-vocabulary alias


class Router(_RouteMixin, fastapi.APIRouter):
    """Optional grouping of workflows with shared dependencies + prefix."""


Workflow = Router  # workflow-vocabulary alias of Router
Task = fastapi.Depends  # workflow-vocabulary alias of fastapi.Depends
