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


class WindowNotFoundError(u.HMError):
    """Game window not found"""


def activate_window(title: str) -> pywinctl.Window:
    windows = pywinctl.getWindowsWithTitle(title)
    if not windows:
        raise WindowNotFoundError("No window titled %r, is game running?", title)
    if len(windows) > 1:
        raise u.HMError("More than one window titled %r", title)
    win = windows[0]
    if win.isActive:
        return win
    if not win.activate(wait=True):
        log.warning("Could not activate window %r %s", win.title, win)
    return win


def get_window_bbox(window: pywinctl.Window) -> pywinctl.Rect:
    return pywinctl.Rect(*window.topleft, *window.bottomright)


def get_screen_size() -> pywinctl.Size:
    return pywinctl.getScreenSize()


def take_screenshot(bbox: t.Optional[BBox] = None) -> PIL.Image:
    return PIL.ImageGrab.grab(bbox, xdisplay="")


def _patch_ewmh():
    import sys
    if not sys.platform == "linux":
        return
    import types
    import ewmh
    import pywinctl

    def setactivewindow(self, win):
        self._setProperty('_NET_ACTIVE_WINDOW', [2, ewmh.ewmh.X.CurrentTime, win.id], win)

    # noinspection PyProtectedMember
    obj = pywinctl._pywinctl_linux.EWMH
    obj.setActiveWindow = types.MethodType(setactivewindow, obj)


_patch_ewmh()
