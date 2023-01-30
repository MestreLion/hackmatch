# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
General utilities
"""
import enum
import logging
import os
import subprocess
import sys
import time
import typing as t

log = logging.getLogger(__name__)

# Windows
if sys.platform == "win32":

    def _run_file(path: str) -> None:
        os.startfile(path)


# macOS
elif sys.platform == "darwin":

    def _run_file(path: str) -> None:
        subprocess.run(("open", path), capture_output=True, check=True, shell=True)


# Linux and variants
else:

    def _run_file(path: str) -> None:
        subprocess.run(("xdg-open", path), capture_output=True, check=True)


class HMError(Exception):
    """Base class for custom exceptions with a few extras on top of Exception.

    - %-formatting for args, similar to logging.log()
    - `errno` numeric attribute, similar to OSError
    - `e` attribute for the original exception, when re-raising exceptions

    All modules in this package raise this (or a subclass) for all
    explicitly raised, business-logic, expected or handled exceptions
    """

    def __init__(
        self, msg: object = "", *args: object, errno: int = 0, e: t.Optional[Exception] = None
    ):
        super().__init__((str(msg) % args) if args else msg)
        self.errno: int = errno
        self.e: t.Optional[Exception] = e


class RunFileError(HMError):
    """Exception for run_file() errors"""


# For value-based Enum.___contains__() alternatives in Python < 3.12,
# see https://stackoverflow.com/q/43634618/624066
# - return isinstance(item, cls) or any(item == i.value for i in cls)
# - return item in set(i.value for i in cls) | set (cls)  # caching sets
Enum = enum.Enum


class BytesEnum(bytes, enum.Enum):
    @classmethod
    def match(cls, value: bytes) -> "BytesEnum":
        return next((item for item in cls if item == value), cls(b""))


class FrameRateLimiter:
    def __init__(self, fps: float = 60):
        self.fps: float = fps
        self._start = time.perf_counter()

    def sleep(self) -> float:
        start = self._start
        now = time.perf_counter()
        diff = 1.0 / self.fps - (now - start)
        if diff > 0:
            time.sleep(diff)
        self._start = time.perf_counter()
        return self._start - start


class Timer:
    def __init__(self, secs: float):
        self.start: float = time.perf_counter()
        self.secs: float = secs

    @property
    def expired(self) -> bool:
        return time.perf_counter() - self.start > self.secs


def benchmark(
    func: t.Callable, *args: object, count: int = 100, **kwargs: object  # type: ignore
) -> None:
    start = time.time()
    for _ in range(count):
        func(*args, **kwargs)
    delta = time.time() - start
    fps = count / delta
    avg = 1000 * delta / count
    print(f"{fps:6.2f} FPS, {avg:5.1f}ms avg: {func.__name__}")


def run_file(path: str) -> None:
    try:
        _run_file(path)
    except (NotImplementedError, subprocess.CalledProcessError) as e:
        raise RunFileError("%s: %s", e.__class__.__name__, e, e=e)
