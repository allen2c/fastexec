import json
import typing

import pydantic


def dict_to_asgi_headers(
    headers: typing.Mapping[str, str],
) -> typing.List[typing.Tuple[bytes, bytes]]:
    return [
        (k.lower().encode("latin1"), v.encode("latin1")) for k, v in headers.items()
    ]


def to_query_params(
    data: typing.Optional[
        typing.Union[typing.Dict, pydantic.BaseModel, str, bytes]
    ] = None,
) -> typing.Mapping[str, typing.Any]:
    if data is None:
        return {}
    elif isinstance(data, pydantic.BaseModel):
        return json.loads(data.model_dump_json())
    elif isinstance(data, typing.Dict):
        return json.loads(json.dumps(data, default=str))
    elif isinstance(data, str):
        return json.loads(data)
    elif isinstance(data, bytes):
        return json.loads(data)
    return json.loads(json.dumps(dict(data), default=str))  # type: ignore


def to_headers(
    data: typing.Optional[
        typing.Union[typing.Dict, pydantic.BaseModel, str, bytes]
    ] = None,
) -> typing.Mapping[str, str]:
    if data is None:
        return {}
    elif isinstance(data, pydantic.BaseModel):
        return {k: str(v) for k, v in json.loads(data.model_dump_json()).items()}
    elif isinstance(data, typing.Dict):
        return {k: str(v) for k, v in data.items()}
    elif isinstance(data, str):
        return {k: str(v) for k, v in json.loads(data).items()}
    elif isinstance(data, bytes):
        return {k: str(v) for k, v in json.loads(data).items()}
    return {k: str(v) for k, v in dict(data).items()}  # type: ignore


def to_body(
    data: typing.Optional[
        typing.Union[typing.Dict, pydantic.BaseModel, str, bytes]
    ] = None,
) -> typing.Dict[str, typing.Any] | bytes:
    if data is None:
        return {}
    elif isinstance(data, pydantic.BaseModel):
        return json.loads(data.model_dump_json())
    elif isinstance(data, typing.Dict):
        return json.loads(json.dumps(data, default=str))
    elif isinstance(data, str):
        return json.loads(data)
    elif isinstance(data, bytes):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    return json.loads(json.dumps(dict(data), default=str))  # type: ignore
