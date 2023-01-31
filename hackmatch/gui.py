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

from . import ai
from . import util as u


BBox: u.TypeAlias = t.Tuple[int, int, int, int]
Size: u.TypeAlias = t.Tuple[int, int]
Image: u.TypeAlias = PIL.Image.Image
Window: u.TypeAlias = pywinctl.Window

log = logging.getLogger(__name__)


class Block(u.BytesEnum):
    EMPTY = b""
    YELLOW = b"a"
    GREEN = b"g"
    RED = b"r"
    PINK = b"p"
    BLUE = b"b"

    def to_ai(self) -> ai.Block:
        return self.name[0] if self.value else ai.EMPTY


class WindowNotFoundError(u.HMError):
    """Game window not found"""


class GameWindow:
    def __init__(self, window: Window):
        self.window: Window = window
        self.offset: t.List[int] = [0, 0]

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
        try:
            return pywinctl.Rect(*self.window.topleft, *self.window.bottomright)
        except Exception as e:
            raise WindowNotFoundError("Window closed: %s", e.__class__.__name__)

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

    def take_screenshot(self) -> Image:
        bbox: BBox = self.bbox
        log.debug("Taking window screenshot: %s", bbox)
        return PIL.ImageGrab.grab(bbox, xdisplay="")

    def close(self) -> None:
        log.info("Closing game")
        self.window.close()

    def to_board(self) -> ai.Board:
        board = ai.Board()
        img: Image = self.take_screenshot()
        y_offset: int = find_y_offset(img)
        return board

    def apply_moves(self, moves: t.List[ai.Move]) -> None:
        ...


def find_y_offset(img: Image) -> int:
    return 0


def get_screen_size() -> Size:
    return pywinctl.getScreenSize()


# Not needed in pywinctl > 0.0.42
def _patch_ewmh() -> None:
    # noinspection PyProtectedMember
    from pywinctl._pywinctl_linux import EWMH as EWMH

    def setactivewindow(self: EWMH, win: t.Any) -> None:
        self._setProperty("_NET_ACTIVE_WINDOW", [2, 0, win.id], win)

    EWMH.setActiveWindow = types.MethodType(setactivewindow, EWMH)


if u.LINUX:
    import types
    _patch_ewmh()
