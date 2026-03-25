from fastexec._exec import FastExec, get_dependant
from fastexec._pipeline import Pipeline
from fastexec.version import version

__version__ = version
__all__ = [
    "get_dependant",
    "FastExec",
    "Pipeline",
]
