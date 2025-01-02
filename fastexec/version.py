import functools
import pathlib
import typing


@functools.lru_cache(maxsize=1)
def get_version() -> typing.Text:
    ver_txt_file = pathlib.Path(__file__).parent.joinpath("VERSION")
    if not ver_txt_file.is_file():
        raise FileNotFoundError(f"Version file not found: {ver_txt_file}")
    return ver_txt_file.read_text().strip()
