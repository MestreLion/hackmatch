# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
General utilities
"""

import logging
import platform
import os
import subprocess
import time

log = logging.getLogger(__name__)


class HMError(Exception):
    """Base class for custom exceptions, with errno and %-formatting for args.

    All modules in this package raise this (or a subclass) for all
    explicitly raised, business-logic, expected or handled exceptions
    """
    def __init__(self, msg: object = "", *args, errno: int = 0):
        super().__init__((str(msg) % args) if args else msg)
        self.errno = errno


class FrameRateLimiter:
    def __init__(self, fps: float = 60):
        self.fps: float = fps
        self._t0 = time.perf_counter()

    def sleep(self) -> float:
        t0 = self._t0
        t1 = time.perf_counter()
        diff = 1.0 / self.fps - (t1 - t0)
        if diff > 0:
            time.sleep(diff)
        self._t0 = time.perf_counter()
        return self._t0 - t0


def open_file(path):
    if platform.system() == 'Windows':   # Windows
        os.startfile(path)
    elif platform.system() == 'Darwin':  # macOS
        subprocess.run(('open', path), shell=True)
    else:                                # linux variants
        subprocess.run(('xdg-open', path))
