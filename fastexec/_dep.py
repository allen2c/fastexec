import typing

import fastapi.dependencies.models
import fastapi.dependencies.utils


def get_dependant(
    *, path: typing.Text = "/", call: typing.Callable
) -> fastapi.dependencies.models.Dependant:
    return fastapi.dependencies.utils.get_dependant(path=path, call=call)
