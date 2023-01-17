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

    def __str__(self):
        return str(self.window)

    @classmethod
    def find_by_title(cls, title: str) -> 'GameWindow':
        windows = pywinctl.getWindowsWithTitle(title)
        if not windows:
            raise WindowNotFoundError("No window titled %r, is the game running?", title)
        if len(windows) > 1:
            raise u.HMError("More than one window titled %r: %s", title, windows)
        window = cls(windows[0])
        log.info("Game window: %s", window)
        return window

    @property
    def bbox(self) -> BBox:
        # return self.window.bbox  # in PyWinCtl >= 0.43
        return pywinctl.Rect(*self.window.topleft, *self.window.bottomright)

    @property
    def size(self) -> Size:
        return tuple(self.window.size)

    def activate(self) -> bool:
        if self.window.isActive or self.window.activate(wait=True):
            return True
        log.warning("Failed to activate window %s", self.window)
        return False

    def take_screenshot(self) -> PIL.Image:
        self.activate()
        bbox = self.bbox
        log.debug("Taking window screenshot: %s", bbox)
        return PIL.ImageGrab.grab(bbox, xdisplay="")

    def close(self):
        log.info("Closing game")
        self.window.close()


def get_screen_size() -> Size:
    return pywinctl.getScreenSize()


def _patch_ewmh():
    import sys
    if not sys.platform == "linux":
        return
    import types
    import ewmh
    import pywinctl

    def setactivewindow(self, win):
        wid = self.getActiveWindow().id
        self._setProperty('_NET_ACTIVE_WINDOW', [1, ewmh.ewmh.X.CurrentTime, wid], win)

    # noinspection PyProtectedMember
    obj = pywinctl._pywinctl_linux.EWMH
    obj.setActiveWindow = types.MethodType(setactivewindow, obj)


_patch_ewmh()
