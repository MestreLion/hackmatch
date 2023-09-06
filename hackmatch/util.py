# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
General utilities
"""
import logging
import os
import subprocess
import sys
import time
import typing as t

if sys.version_info < (3, 10):
    # noinspection PyUnresolvedReferences
    from typing_extensions import TypeAlias as TypeAlias
else:
    # noinspection PyUnresolvedReferences
    from typing import TypeAlias as TypeAlias

try:
    # Disable Pygame advertisement. Must be done before importing it
    # https://github.com/pygame/pygame/commit/18a31449de93866b369893057f1e60330b53da95
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = ""  # the key just need to exist
    import pygame as pygame

    HAVE_PYGAME = True
except ImportError:
    HAVE_PYGAME = False


# Dummy to make mypy happy. Will be overriden on Windows platforms
def my_documents_path(suffix: str = "") -> str:
    return os.path.join("~/Documents", suffix)


# Platform detection
# Bool constants used to encapsulate detection method, currently sys.platform
# Windows
if sys.platform == "win32":
    WINDOWS = True
    MACOS = False
    LINUX = False

    def _run_file(path: str) -> None:
        os.startfile(path)

    import ctypes, ctypes.wintypes

    # noinspection PyPep8Naming
    def my_documents_path(suffix: str = "") -> str:
        # Adapted from https://stackoverflow.com/a/30924555/624066
        # Default path in Vista/Win7 and above:
        # ~/Documents = %USERPROFILE%\Documents = C:\Users\<user>\Documents
        # Current path might be different, e.g. '~/OneDrive/Documents'
        # See also:
        # https://stackoverflow.com/a/20079912/624066
        # https://learn.microsoft.com/en-us/windows/win32/shell/csidl
        # https://github.com/wine-mirror/wine/blob/master/include/shlobj.h
        # https://github.com/ActiveState/appdirs/blob/master/appdirs.py
        CSIDL_PERSONAL = 5  # 'My Documents', ~/Documents by default
        SHGFP_TYPE_CURRENT = 0  # 0 for current path, 1 for default path
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(
            None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf
        )
        return os.path.join(buf.value, suffix)


# macOS
elif sys.platform == "darwin":
    WINDOWS = False
    MACOS = True
    LINUX = False

    def _run_file(path: str) -> None:
        subprocess.run(("open", path), capture_output=True, check=True, shell=True)


# Linux and variants
else:
    WINDOWS = False
    MACOS = False
    LINUX = True

    def _run_file(path: str) -> None:
        try:
            # Timeout to safeguard against xdg-open blocking until launched application exits
            subprocess.run(("xdg-open", path), capture_output=True, check=True, timeout=1)
        except subprocess.TimeoutExpired:
            pass


_T = t.TypeVar("_T")  # general-use


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


class FileOpenError(HMError, FileNotFoundError):
    """File not found or otherwise unable to open"""


class Terminal:
    # https://stackoverflow.com/a/50560686/624066
    CLEAR: str = "\033[2J\033[H"
    RESET: str = "\033c"  # or CLEAR + "\033[3J"


class FrameRateLimiter:
    def __init__(self, fps: float = 60):
        self.fps: float = fps
        self._start = time.perf_counter()

    def wait(self) -> float:
        start = self._start
        if self.fps > 0:
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
    def remaining(self) -> float:
        return self.secs - (time.perf_counter() - self.start)  # or secs - elapsed

    @property
    def elapsed(self) -> float:
        return time.perf_counter() - self.start  # or secs - remaining

    @property
    def expired(self) -> bool:
        return self.remaining < 0

    def wait(self) -> float:
        remaining = self.remaining
        if remaining < 0:
            return 0
        time.sleep(remaining)
        return remaining


class Clock(Timer):
    def __init__(self) -> None:
        super().__init__(0)

    @property
    def expired(self) -> bool:
        return False


def chunked(data: t.Sequence[_T], chunk_size: int) -> t.Iterator[t.Tuple[_T, ...]]:
    # Adapted from https://stackoverflow.com/a/312464/624066
    return (tuple(data[i : i + chunk_size]) for i in range(0, len(data), chunk_size))


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


def setup_logging(
    level: int = logging.INFO,
    fmt: str = "[%(asctime)s %(levelname)-6.6s] %(module)-4s: %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
    style: t.Literal["%", "{", "$"] = "%",
) -> None:
    if level < logging.INFO:
        logging.basicConfig(level=level, format=fmt, datefmt=datefmt, style=style)
        return

    # Adapted from https://stackoverflow.com/a/25101727/624066
    class PlainInfo(logging.Formatter):
        info_formatter = logging.Formatter(style=style)

        def format(self, record: logging.LogRecord) -> str:
            if record.levelno == logging.INFO:
                return self.info_formatter.format(record)
            return super().format(record)

    handler = logging.StreamHandler()
    handler.setFormatter(PlainInfo(fmt=fmt, datefmt=datefmt, style=style))
    logging.basicConfig(level=level, handlers=[handler])
