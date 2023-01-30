# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
GUI Input and Output
"""

import logging
import typing as t

import PIL.Image, PIL.ImageGrab
import pywinctl

from . import util as u


log = logging.getLogger(__name__)

BBox: 't.TypeAlias' = t.Tuple[int, int, int, int]
Size: 't.TypeAlias' = t.Tuple[int, int]


class WindowNotFoundError(u.HMError):
    """Game window not found"""


class GameWindow:
    def __init__(self, window: pywinctl.Window):
        self.window: pywinctl.Window = window

    def __str__(self) -> str:
        return str(self.window)

    @classmethod
    def find_by_title(cls, title: str) -> "GameWindow":
        windows = pywinctl.getWindowsWithTitle(title)
        if not windows:
            raise WindowNotFoundError("No window titled %r, is the game running?", title)
        if len(windows) > 1:
            log.warning("More than one window titled %r: %s", title, windows)
        window = cls(windows[0])
        return window

    @property
    def bbox(self) -> BBox:
        # return self.window.bbox  # in PyWinCtl >= 0.43
        return pywinctl.Rect(*self.window.topleft, *self.window.bottomright)

    @property
    def size(self) -> Size:
        return self.window.size

    def activate(self, reposition: bool = True) -> bool:
        if self.window.isActive or self.window.activate(wait=True):
            if reposition:
                self.window.moveTo(0, 0)
            return True
        log.warning("Failed to activate window %s", self.window)
        return False

    def take_screenshot(self) -> PIL.Image:
        bbox = self.bbox
        log.debug("Taking window screenshot: %s", bbox)
        return PIL.ImageGrab.grab(bbox, xdisplay="")

    def close(self) -> None:
        log.info("Closing game")
        self.window.close()


def get_screen_size() -> Size:
    return pywinctl.getScreenSize()


# Not needed in pywinctl > 0.0.42
def _patch_ewmh() -> None:
    import sys

    if not sys.platform == "linux":
        return
    import types

    # noinspection PyProtectedMember
    from pywinctl._pywinctl_linux import EWMH as EWMH

    def setactivewindow(self: EWMH, win: t.Any) -> None:
        self._setProperty("_NET_ACTIVE_WINDOW", [2, 0, win.id], win)

    EWMH.setActiveWindow = types.MethodType(setactivewindow, EWMH)

_patch_ewmh()
