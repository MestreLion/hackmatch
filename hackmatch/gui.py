# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
GUI Input and Output
"""

import logging
import typing as t

import PIL.Image, PIL.ImageGrab, PIL.ImageDraw
import pywinctl

from . import ai
from . import config as c
from . import util as u


log = logging.getLogger(__name__)

_BT = t.TypeVar("_BT", bound="BaseBlock")
BBox: u.TypeAlias = t.Tuple[int, int, int, int]  # left, top, right, bottom
Size: u.TypeAlias = t.Tuple[int, int]  # width, height
Offset: u.TypeAlias = t.Tuple[int, int]  # x, y
Image: u.TypeAlias = PIL.Image.Image
Window: u.TypeAlias = pywinctl.Window

BPP: int = 3  # Bits per pixel in Image data (bit depth)
MATCH_PIXELS = 10  # Pixels in a row to consider a block match


class BaseBlock(bytes, u.Enum):
    @classmethod
    def match(cls: t.Type[_BT], value: bytes, repeat: int = 8) -> _BT:
        return next((item for item in cls if repeat * item == value), cls(b""))

    def to_ai(self) -> ai.Block:
        return self.name[0] if self.value else ai.EMPTY


# fmt: off
class Parameters:
    """Base class, declaring parameters"""
    GAME_SIZE: Size = (0, 0)  # Expected Window and screenshot image size
    BLOCK_SIZE: Size = (0, 0)  # Block Size
    OFFSET: Offset = (0, 0)  # Leftmost block start, Top "shadow" ends + 1
    HEIGHT: int = 0  # Board height, including Phage. OFFSET[1] + HEIGHT = Ground
    MATCH_Y_OFFSET: int = 0  # Offset from block top to match marker
    # Derived
    WIDTH: int = 0  # Board width, BLOCK_SIZE[0] * BOARD_COLS
    MATCH_X_OFFSET: int = 0  # Offset from block left using BLOCK_SIZE and MATCH_PIXELS
    BLOCKS_Y_RANGE: t.Tuple[int, int, int] = (0, 0, 0)  # Range for finding Y offset

    class Block(BaseBlock):
        # For 1920x1080
        EMPTY  = b""
        YELLOW = b"\xeb\xa3\x18"  # RGB(235, 163,  24), HSV( 40, 90, 86+6=92)
        GREEN  = b"\x12\xba\x9c"  # RGB( 18, 186, 156), HSV(169, 90, 68+5=73)
        RED    = b"\xdc\x17\x31"  # RGB(220,  23,  49), HSV(352, 90, 80+6=86), R=219, G=22
        PINK   = b"\xfb\x17\xb8"  # RGB(251,  23, 184), HSV(317, 91, 92+6=98), R=250, G=22
        BLUE   = b"\x20\x39\x82"  # RGB( 32,  57, 130), HSV(255, 75, 47+4=51)

    @classmethod
    def x(cls, col: int) -> int:
        if not 0 <= col < c.BOARD_COLS:
            raise InvalidValue("Invalid column: %s", col)
        return cls.OFFSET[0] + col * cls.BLOCK_SIZE[0] + cls.MATCH_X_OFFSET

    @classmethod
    def y(cls, row: int, y_offset: int) -> int:
        if not 0 <= row < c.BOARD_ROWS:
            raise InvalidValue("Invalid row: %s", row)
        if not 0 <= y_offset < cls.BLOCK_SIZE[1]:
            raise InvalidValue("Invalid y offset: %s", y_offset)
        return cls.OFFSET[1] + row * cls.BLOCK_SIZE[1] + y_offset


class Parameters1920x1080(Parameters):
    BLOCK_SIZE = (72, 72)
    OFFSET = (440, 151)  # Leftmost block start, Top "shadow" ends + 1
    HEIGHT = 770  # Board height, including Phage. OFFSET[1] + HEIGHT = Ground
    MATCH_Y_OFFSET = 56  # Offset from block top to match marker


class Parameters1920x1200(Parameters1920x1080):
    OFFSET = (440, 211)


class Parameters1600x900(Parameters):
    BLOCK_SIZE = (60, 60)
    OFFSET = (367, 126)
    HEIGHT = 643
    MATCH_Y_OFFSET = 46


class Parameters1366x768(Parameters):
    BLOCK_SIZE = (51, 51)
    OFFSET = (313, 107)
    HEIGHT = 548
    MATCH_Y_OFFSET = 40


PARAMETERS: t.Dict[Size, t.Type[Parameters]] = {
    (1920, 1080): Parameters1920x1080,
    (1920, 1200): Parameters1920x1200,
    (1600,  900): Parameters1600x900,
    (1366,  768): Parameters1366x768,
}
# fmt: on


class WindowNotFoundError(u.HMError):
    """Game window not found"""


class InvalidValue(u.HMError, ValueError):
    """Invalid or out-of-bounds value for col, row, x, y, ..."""


class GameWindow:
    def __init__(self, window: Window):
        self.window: Window = window
        self.prev_size: Size = self.size
        self.board: ai.Board = ai.Board()

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

    def to_board(self) -> ai.Board:
        if not c.args.path:
            img: Image = self.take_screenshot()
        else:
            img = PIL.Image.open(c.args.path).convert(mode="RGB")
        size = img.size
        if size != self.prev_size:
            log.info("Game window resized: %s", self)
            self.prev_size = size
        # TODO: catch HMError and warn the first time, start timer to re-raise
        params = get_parameters(size)
        data: bytes = img.tobytes()
        assert len(data) == size[0] * size[1] * BPP
        y_offset = find_y_offset(data, params)
        if y_offset < 0:
            return ai.Board()

        board: ai.Board = ai.Board()
        for row in range(c.BOARD_ROWS):
            for col in range(c.BOARD_COLS):
                block = get_block_at(data, params, col, row, y_offset)
                board.set_block(col, row, block.to_ai())

        if board != self.board:
            self.board = board
            if c.args.debug:
                draw_debug(img, params, y_offset).save(
                    f"debug_{size[1]}_{y_offset}_{board.serialize()}.png"
                )
        return board

    def apply_moves(self, moves: t.List[ai.Move]) -> None:
        ...


def draw_debug(original: Image, p: t.Type[Parameters], y_offset: int) -> Image:
    img = original.copy()
    data = original.tobytes()
    draw = PIL.ImageDraw.Draw(img)
    for row in range(c.BOARD_ROWS):
        y = p.y(row, y_offset)
        draw.rectangle((0, y - 1, img.size[0], y + 1))
        for col in range(c.BOARD_COLS):
            x = p.x(col)
            draw.rectangle((x - 1, y - 1, x + MATCH_PIXELS + 1, y + 1))
            block = get_block_at(data, p, x=x, y=y)
            if block == p.Block.EMPTY:
                continue
            color = t.cast(t.Tuple[int, int, int], tuple(block.value[:3]))
            w, h = p.BLOCK_SIZE
            x1 = x - p.MATCH_X_OFFSET
            y1 = y - p.MATCH_Y_OFFSET
            x2 = x1 + w - 1
            y2 = y1 + h - 1
            dx, dy = w // 4, h // 4
            draw.rectangle((x1, y1, x2, y2), outline=color)
            draw.rectangle((x1 + dx, y1 + dy, x2 - dx, y2 - dy), fill=color)
    return img.crop(
        (p.OFFSET[0], p.BLOCKS_Y_RANGE[1], p.OFFSET[0] + p.WIDTH, p.BLOCKS_Y_RANGE[0])
    )


def find_y_offset(data: bytes, p: t.Type[Parameters]) -> int:
    for y in range(*p.BLOCKS_Y_RANGE):
        for col in range(c.BOARD_COLS):
            x = p.x(col)
            block = get_block_at(data, p, x=x, y=y)
            if block is p.Block.EMPTY:
                continue
            row, y_offset = divmod(y - p.BLOCKS_Y_RANGE[1], p.BLOCK_SIZE[1])
            log.debug("Y Offset: %2s, Pixel%s Board%s %s",
                      y_offset, (x, y), (col, row), block)  # fmt: skip
            return y_offset
    return -1


# fmt: off
def get_block_at(
    data: bytes,
    p: t.Type[Parameters],
    col: int = -1, row: int = -1, y_offset: int = -1,
    x: int = -1, y: int = -1,
) -> Parameters.Block:
    if x < 0: x = p.x(col)
    if y < 0: y = p.y(row, y_offset)
    d = BPP * (p.GAME_SIZE[0] * y + x)
    # TODO: replace resolution-quirk "aliases"
    return p.Block.match(data[d : d + MATCH_PIXELS * BPP], MATCH_PIXELS)
# fmt: on


def get_screen_size() -> Size:
    return pywinctl.getScreenSize()


def get_parameters(size: Size) -> t.Type[Parameters]:
    cls = PARAMETERS.get(size)
    if cls is None:
        raise u.HMError(
            "Unsupported game window size: %s, must be one of %s",
            size,
            tuple(PARAMETERS.keys()),
        )
    if cls.GAME_SIZE == (0, 0):
        cls.GAME_SIZE = size
        # Derived constants
        cls.WIDTH = cls.BLOCK_SIZE[0] * c.BOARD_COLS
        cls.MATCH_X_OFFSET = (cls.BLOCK_SIZE[0] - MATCH_PIXELS) // 2
        cls.BLOCKS_Y_RANGE = (
            cls.OFFSET[1] + cls.BLOCK_SIZE[1] * c.BOARD_ROWS,
            cls.OFFSET[1],
            -1,
        )
    return cls


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
