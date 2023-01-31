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
from . import config as c
from . import util as u


BBox: u.TypeAlias = t.Tuple[int, int, int, int]
Size: u.TypeAlias = t.Tuple[int, int]
Image: u.TypeAlias = PIL.Image.Image
Window: u.TypeAlias = pywinctl.Window

BPP: int = 3  # Bits per pixel in Image data (bit depth)


class Offsets:
    BLOCK_SIZE = (72, 72)
    BOARD_OFFSET = (440, 150)
    BOARD_HEIGHT = 770
    BOARD_WIDTH = BLOCK_SIZE[0] * c.BOARD_COLS


OFFSETS = {
    1920: Offsets,
    1600: None,
    1366: None,
}
# for _cls in OFFSETS.values():
#     _cls.BOARD_WIDTH = _cls.BLOCK_SIZE[0] * c.BOARD_COLS

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
            raise WindowNotFoundError("Game window closed [%s]", e.__class__.__name__)

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
        image = PIL.ImageGrab.grab(bbox, xdisplay="")  # RGBA in macOS
        if image.mode != "RGB":
            image = image.convert(mode="RGB")
        return image

    def close(self) -> None:
        log.info("Closing game")
        self.window.close()

    def to_board(self, path: t.Optional[str] = None) -> ai.Board:
        board = ai.Board()
        if not path:
            img: Image = self.take_screenshot()
        else:
            img = PIL.Image.open(path).convert(mode="RGB")
        width, height = img.size
        offsets = OFFSETS.get(width)
        if offsets is None:
            raise u.HMError(
                "Unsupported image width: %s, must be one of %s",
                width,
                tuple(OFFSETS.keys()),
            )
        data: bytes = img.tobytes()
        assert len(data) == width * height * BPP
        y_offset: int = find_y_offset(data, width, height, offsets)
        return board

    def apply_moves(self, moves: t.List[ai.Move]) -> None:
        ...


def find_y_offset(data: bytes, width: int, height: int, o: t.Type[Offsets]) -> int:
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
