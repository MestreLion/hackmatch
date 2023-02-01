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


log = logging.getLogger(__name__)

BBox: u.TypeAlias = t.Tuple[int, int, int, int]  # left, top, right, bottom
Size: u.TypeAlias = t.Tuple[int, int]  # width, height
Offset: u.TypeAlias = t.Tuple[int, int]  # x, y
Image: u.TypeAlias = PIL.Image.Image
Window: u.TypeAlias = pywinctl.Window

BPP: int = 3  # Bits per pixel in Image data (bit depth)
MATCH_PIXELS = 10  # Pixels in a row to consider a block match


class BoardParams1920x1080:
    BLOCK_SIZE: Size = (72, 72)
    BLOCK_X_OFFSET: int = 30  # From block left to marker
    OFFSET: Offset = (440, 151)  # Leftmost block start, Top "shadow" ends
    HEIGHT: int = 770  # Play area including Phage. OFFSET[1] + HEIGHT == Ground
    WIDTH: int = 0
    BLOCKS_Y_RANGE: t.Tuple[int, int, int] = (0, 0, 0)


class BoardParams1920x1200(BoardParams1920x1080):
    OFFSET = (440, 211)


class BoardParams1600x900(BoardParams1920x1080):
    BLOCK_SIZE = (60, 60)
    BLOCK_X_OFFSET = 22
    OFFSET = (367, 126)
    HEIGHT = 643


class BoardParams1366x768(BoardParams1920x1080):
    BLOCK_SIZE = (51, 51)
    BLOCK_X_OFFSET = 20
    OFFSET = (313, 107)
    HEIGHT = 548


BOARD_PARAMS = {
    # fmt: off
    (1920, 1080): BoardParams1920x1080,
    (1920, 1200): BoardParams1920x1200,
    (1600,  900): BoardParams1600x900,
    (1366,  768): BoardParams1366x768,
    # fmt: on
}
for _cls in BOARD_PARAMS.values():
    if _cls is None:
        continue
    _cls.WIDTH = _cls.BLOCK_SIZE[0] * c.BOARD_COLS
    _cls.BLOCKS_Y_RANGE = (
        _cls.OFFSET[1] + _cls.BLOCK_SIZE[1] * c.BOARD_ROWS,
        _cls.OFFSET[1],
        -1,
    )


class Block(u.BytesEnum):
    EMPTY = b""
    # fmt: off
    YELLOW = b"\xeb\xa3\x18"  # RGB(235, 163,  24), HSV( 40, 90, 86+6=92)
    GREEN  = b"\x12\xba\x9c"  # RGB( 18, 186, 156), HSV(169, 90, 68+5=73)
    RED    = b"\xdc\x17\x31"  # RGB(220,  23,  49), HSV(352, 90, 80+6=86), R=219, G=22
    PINK   = b"\xfb\x17\xb8"  # RGB(251,  23, 184), HSV(317, 91, 92+6=98), R=250, G=22
    BLUE   = b"\x20\x39\x82"  # RGB( 32,  57, 130), HSV(255, 75, 47+4=51)
    # fmt: on

    def to_ai(self) -> ai.Block:
        return self.name[0] if self.value else ai.EMPTY


class WindowNotFoundError(u.HMError):
    """Game window not found"""


class GameWindow:
    def __init__(self, window: Window):
        self.window: Window = window
        self.offset: t.List[int] = [0, 0]
        self.prev_size: Size = self.size

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
        if (width, height) != self.prev_size:
            log.info("Game window resized: %s", self)
            self.prev_size = (width, height)
        params = BOARD_PARAMS.get((width, height))
        if params is None:
            raise u.HMError(
                "Unsupported game window size: %s, must be one of %s",
                width,
                tuple(BOARD_PARAMS.keys()),
            )
        data: bytes = img.tobytes()
        assert len(data) == width * height * BPP
        y_offset, block_col, block_row, block = find_y_offset(data, width, params)

        for row in range(c.BOARD_ROWS):
            y = params.OFFSET[1] + row * params.BLOCK_SIZE[1] + y_offset
            for col in range(c.BOARD_COLS):
                block, x = get_block_at(data, col, y, width, params)
                board.set_block(col, row, block.to_ai())
        return board

    def apply_moves(self, moves: t.List[ai.Move]) -> None:
        ...


def find_y_offset(
    data: bytes, width: int, p: t.Type[BoardParams1920x1080]
) -> t.Tuple[int, int, int, Block]:
    for y in range(*p.BLOCKS_Y_RANGE):
        for col in range(c.BOARD_COLS):
            block, x = get_block_at(data, col, y, width, p)
            if block is Block.EMPTY:
                continue
            row, y_offset = divmod(y - p.BLOCKS_Y_RANGE[1], p.BLOCK_SIZE[1])
            log.info("Board Y Offset: %2s, Pixel%s Board%s %s",
                     y_offset, (x, y), (col, row), block)  # fmt: skip
            return y_offset, col, row, block
    return -1, -1, -1, Block.EMPTY


def get_block_at(data, col, y, width, p):
    x = p.OFFSET[0] + col * p.BLOCK_SIZE[0] + p.BLOCK_X_OFFSET
    d = BPP * (width * y + x)
    return Block.match(data[d : d + MATCH_PIXELS * BPP], MATCH_PIXELS), x


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
