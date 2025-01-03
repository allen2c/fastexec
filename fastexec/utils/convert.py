import typing


def dict_to_asgi_headers(
    headers: typing.Mapping[typing.Text, typing.Text]
) -> typing.List[typing.Tuple[bytes, bytes]]:
    return [
        (k.lower().encode("latin1"), v.encode("latin1")) for k, v in headers.items()
    ]
