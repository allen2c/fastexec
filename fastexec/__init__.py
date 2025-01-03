from fastexec._dep import get_dependant
from fastexec._exec import FastExec, exec_with_dependant
from fastexec.version import get_version

__version__ = get_version()
__all__ = [
    "get_dependant",
    "exec_with_dependant",
    "FastExec",
]
