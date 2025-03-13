import json
import logging
import typing

import pydantic

logger = logging.getLogger("fastexec")


JSONSerializable = typing.Union[
    typing.Dict[typing.Text, typing.Any],
    typing.List[typing.Any],
    typing.Text,
    int,
    float,
    bool,
    None,
]
JSONObject = typing.Union[typing.Dict, pydantic.BaseModel, typing.Text, bytes]
QueryParams = typing.Mapping[typing.Text, typing.Any]
Headers = typing.Mapping[typing.Text, typing.Text]
Body = typing.Dict[typing.Text, typing.Any]


def dict_to_asgi_headers(
    headers: typing.Mapping[typing.Text, typing.Text],
) -> typing.List[typing.Tuple[bytes, bytes]]:
    return [
        (k.lower().encode("latin1"), v.encode("latin1")) for k, v in headers.items()
    ]


def to_query_params(data: typing.Optional[JSONObject] = None) -> QueryParams:
    if data is None:
        return {}
    elif isinstance(data, pydantic.BaseModel):
        return json.loads(data.model_dump_json())
    elif isinstance(data, typing.Dict):
        return json.loads(json.dumps(data, default=str))
    elif isinstance(data, typing.Text):
        return json.loads(data)
    elif isinstance(data, bytes):
        return json.loads(data)
    logger.debug(f"Undefined query params type: {type(data)}, try to convert to dict")
    return json.loads(json.dumps(dict(data), default=str))  # type: ignore


def to_headers(data: typing.Optional[JSONObject] = None) -> Headers:
    if data is None:
        return {}
    elif isinstance(data, pydantic.BaseModel):
        return {k: str(v) for k, v in json.loads(data.model_dump_json()).items()}
    elif isinstance(data, typing.Dict):
        return {k: str(v) for k, v in data.items()}
    elif isinstance(data, typing.Text):
        return {k: str(v) for k, v in json.loads(data).items()}
    elif isinstance(data, bytes):
        return {k: str(v) for k, v in json.loads(data).items()}
    logger.debug(f"Undefined headers type: {type(data)}, try to convert to dict")
    return {k: str(v) for k, v in dict(data).items()}  # type: ignore


def to_body(data: typing.Optional[JSONObject] = None) -> Body | bytes:
    if data is None:
        return {}
    elif isinstance(data, pydantic.BaseModel):
        return json.loads(data.model_dump_json())
    elif isinstance(data, typing.Dict):
        return json.loads(json.dumps(data, default=str))
    elif isinstance(data, typing.Text):
        return json.loads(data)
    elif isinstance(data, bytes):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data  # Is bytes
    logger.debug(f"Undefined body type: {type(data)}, try to convert to dict")
    return json.loads(json.dumps(dict(data), default=str))  # type: ignore
