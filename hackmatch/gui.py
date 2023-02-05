# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
GUI Input and Output
"""

import enum
import logging
import typing as t

import PIL.Image, PIL.ImageGrab, PIL.ImageDraw
import pyautogui
import pywinctl

from . import ai
from . import config as c
from . import game
from . import util as u


log = logging.getLogger(__name__)

_BT = t.TypeVar("_BT", bound="BaseBlock")
BBox: u.TypeAlias = t.Tuple[int, int, int, int]  # left, top, right, bottom
Size: u.TypeAlias = t.Tuple[int, int]  # width, height
Offset: u.TypeAlias = t.Tuple[int, int]  # x, y
Image: u.TypeAlias = PIL.Image.Image
Window: u.TypeAlias = pywinctl.Window
ParamCls: u.TypeAlias = t.Type["Parameters"]

BPP: int = 3  # Bits per pixel in Image data (bit depth)
MATCH_PIXELS = 8  # Pixels in a row to consider a block match

# Delay after each key event (Down and Up), in seconds. Full key press = 2 * PAUSE
pyautogui.PAUSE = 0.017  # 17ms = 60 FPS. Default = 0.1 = 100ms = 10 FPS


class BaseBlock(bytes, enum.Enum):
    # If value-based Enum.___contains__() is needed in Python < 3.12,
    # see alternatives from https://stackoverflow.com/q/43634618/624066
    # - return isinstance(item, cls) or any(item == i.value for i in cls)
    # - return item in set(i.value for i in cls) | set (cls)  # caching sets
    @classmethod
    def match(cls: t.Type[_BT], value: bytes, repeat: int = 8) -> _BT:
        block = next((item for item in cls if repeat * item == value), cls(b""))
        # Handle "aliases": names with a "X*_NAME*" pattern
        if block.name[0] == "X":
            # noinspection PyTypeChecker, buggy PyCharm
            return cls[block.name.split("_", 1)[-1]]
        return block

    def to_ai(self) -> ai.Block:
        return ai.Block[self.name]


# fmt: off
class Parameters:
    """Base class, declaring parameters"""
    GAME_SIZE: Size = (0, 0)  # Expected Window and screenshot image size
    BLOCK_SIZE: Size = (0, 0)  # Block Size
    OFFSET: Offset = (0, 0)  # Leftmost block start, Top "shadow" ends + 1
    HEIGHT: int = 0  # Board height, including Phage. OFFSET[1] + HEIGHT = Ground
    MATCH_Y_OFFSET: int = 0  # Offset from block top to match marker
    PHAGE_OFFSET: Offset = (0, 0)  # Offset from (column left, window top) to phage marker
    PHAGE_DATA: bytes = b'fill me!'
    HELD_Y_OFFSET: int = 0  # Y offset to phage held block marker
    # Derived
    WIDTH: int = 0  # Board width, BLOCK_SIZE[0] * BOARD_COLS
    MATCH_X_OFFSET: int = 0  # Offset from block left using BLOCK_SIZE and MATCH_PIXELS
    BLOCKS_Y_RANGE: t.Tuple[int, int, int] = (0, 0, 0)  # Range for finding Y offset

    class Block(BaseBlock):
        # For 1920x1080
        EMPTY  = b""
        YELLOW = b"\xeb\xa3\x18"  # RGB(235, 163,  24)
        GREEN  = b"\x12\xba\x9c"  # RGB( 18, 186, 156)
        RED    = b"\xdc\x17\x31"  # RGB(220,  23,  49)
        PINK   = b"\xfb\x17\xb8"  # RGB(251,  23, 184)
        BLUE   = b"\x20\x39\x82"  # RGB( 32,  57, 130)
        Y_BOMB = b"\x1d\x1b\x08"  # RGB( 29,  27,   8)
        G_BOMB = b"\x03\x28\x2d"  # RGB(  3,  40,  45)
        R_BOMB = b"\x42\x09\x0f"  # RGB( 66,   9,  15)
        P_BOMB = b"\x3c\x00\x32"  # RGB( 60,   0,  50)
        B_BOMB = b"\x09\x04\x33"  # RGB(  9,   4,  51)

    @classmethod
    def x(cls, col: int) -> int:
        if not 0 <= col < c.BOARD_COLS:
            raise InvalidValueError("Invalid column: %s", col)
        return cls.OFFSET[0] + col * cls.BLOCK_SIZE[0] + cls.MATCH_X_OFFSET

    @classmethod
    def y(cls, row: int, y_offset: int) -> int:
        if not 0 <= row < c.BOARD_ROWS:
            raise InvalidValueError("Invalid row: %s", row)
        if not 0 <= y_offset < cls.BLOCK_SIZE[1]:
            raise InvalidValueError("Invalid y offset: %s", y_offset)
        return cls.OFFSET[1] + row * cls.BLOCK_SIZE[1] + y_offset


class Parameters1920x1080(Parameters):
    BLOCK_SIZE = (72, 72)
    OFFSET = (440, 151)
    HEIGHT = 770
    MATCH_Y_OFFSET = 56


class Parameters1920x1200(Parameters1920x1080):
    OFFSET = (440, 211)

    class Block(BaseBlock):
        YELLOW = b"\xe8\xa1\x17"  # RGB(235, 161,  24)
        GREEN  = b"\x12\xb7\x99"  # RGB( 18, 183, 153)
        RED    = b"\xd9\x16\x30"  # RGB(217,  22,  48)
        PINK   = b"\xf7\x16\xb6"  # RGB(247,  22, 182)
        BLUE   = b"\x20\x38\x80"  # RGB( 32,  56, 128)
        Y_BOMB = b"\x1d\x1a\x07"  # RGB( 29,  26,   7)
        G_BOMB = b"\x03\x27\x2c"  # RGB(  3,  39,  44)
        R_BOMB = b"\x41\x08\x0e"  # RGB( 65,   8,  14)
        P_BOMB = b"\x3b\x00\x32"  # RGB( 59,   0,  50)
        B_BOMB = b"\x08\x04\x33"  # RGB(  8,   4,  51)


class Parameters1600x900(Parameters):
    BLOCK_SIZE = (60, 60)
    OFFSET = (367, 126)
    HEIGHT = 643
    MATCH_Y_OFFSET = 46

    class Block(BaseBlock):
        X_GREEN = b"\x12\xba\x9b"  # RGB( 18, 186, 155)
        G_BOMB  = b"\x03\x28\x2d"  # RGB(  3,  40,  45)


class Parameters1366x768(Parameters):
    BLOCK_SIZE = (51, 51)
    OFFSET = (313, 107)
    HEIGHT = 548
    MATCH_Y_OFFSET = 40

    class Block(BaseBlock):
        X_GREEN = b"\x12\xba\x9b"  # RGB( 18, 186, 155), same as 1600x900
        G_BOMB  = b"\x03\x28\x2d"  # RGB(  3,  40,  45), same as 1920x1200


PARAMETERS: t.Dict[Size, ParamCls] = {
    (1920, 1080): Parameters1920x1080,
    (1920, 1200): Parameters1920x1200,
    (1600,  900): Parameters1600x900,
    (1366,  768): Parameters1366x768,
}
# fmt: on


class WindowNotFoundError(u.HMError):
    """Game window not found"""


class InvalidValueError(u.HMError, ValueError):
    """Invalid or out-of-bounds value for col, row, x, y, etc"""


class UnsupportedWindowSizeError(u.HMError, ValueError):
    """Window size not in PARAMETERS, likely a fluke during window drag"""


class BoardData(t.NamedTuple):
    image: Image
    data: bytes
    parameters: ParamCls
    y_offset: t.Optional[int]
    board: t.Optional[ai.Board]


class GameWindow:
    def __init__(self, window: Window):
        self.window: Window = window
        self.prev_size: Size = self.size
        self.prev_board: t.Optional[ai.Board] = None

        settings: c.GameSettings = game.read_settings()
        self.keymap: t.Dict[ai.Move, str] = {
            move: get_keyname(settings[move.value]) for move in ai.Move
        }
        log.debug("Keymap: %s", self.keymap)

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

    def new_board(self) -> ai.Board:
        fps = 20  # c.config["bot_fps"]
        clock = u.FrameRateLimiter(fps)
        error_count = 0
        while True:
            try:
                *_, board = board_data = self.to_board()
            except UnsupportedWindowSizeError as e:
                # warn every 2 seconds, raise after 10
                if error_count >= 10 * fps:
                    raise
                if error_count % (2 * fps) == 0:
                    log.warning(e)
                error_count += 1
                clock.sleep()
                continue
            if board is not None and board != self.prev_board:
                if c.args.debug:
                    save_debug(board_data)
                self.prev_board = board
                return board
            clock.sleep()

    def to_board(self) -> BoardData:
        if not c.args.path:
            image: Image = self.take_screenshot()
        else:
            image = PIL.Image.open(c.args.path).convert(mode="RGB")
        size = image.size
        if size != self.prev_size:
            log.info("Game window resized: %s", size)
            self.prev_size = size
        # TODO: catch HMError and warn the first time, start timer to re-raise
        return parse_image(image)

    def send_moves(self, moves: t.List[ai.Move]) -> None:
        for move in moves:
            press_key(self.keymap[move])


def parse_image(image: Image) -> BoardData:
    size = image.size
    params = get_parameters(size)
    data: bytes = image.tobytes()
    assert len(data) == size[0] * size[1] * BPP

    y_offset = find_y_offset(data, params)
    if y_offset is None:
        return BoardData(image, data, params, None, None)

    col = find_phage_column(data, params)
    block = find_held_block(data, params, col)

    board = ai.Board(phage_col=col, held_block=block.to_ai())
    for row in range(c.BOARD_ROWS):
        for col in range(c.BOARD_COLS):
            block = get_block_at(data, params, col, row, y_offset)
            board.set_block(col, row, block.to_ai())

    return BoardData(image, data, params, y_offset, board)


def find_y_offset(data: bytes, p: ParamCls) -> t.Optional[int]:
    # TODO: Resolution-specific quirks:
    #  - 1600x900: green RGB varies in the same image, and can match the top.
    #    Do not trust for Y offset
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
    else:
        return None


def find_phage_column(data: bytes, p: ParamCls) -> t.Optional[int]:
    # TODO: It's not that simple...
    for col in range(c.BOARD_COLS):
        x = p.x(col) + p.PHAGE_OFFSET[0]
        y = p.PHAGE_OFFSET[1]
        if get_segment(data, p, x, y, len(p.PHAGE_DATA)) == p.PHAGE_DATA:
            return col
    else:
        return None


def find_held_block(data: bytes, p: ParamCls, phage: t.Optional[int]) -> Parameters.Block:
    # TODO: It's not that simple either...
    if phage is None:
        return p.Block.EMPTY
    return get_block_at(data, p, col=phage, y=p.HELD_Y_OFFSET)


# fmt: off
def get_block_at(
    data: bytes,
    p: ParamCls,
    col: int = -1, row: int = -1, y_offset: int = -1,
    x: int = -1, y: int = -1,
) -> Parameters.Block:
    if x < 0: x = p.x(col)
    if y < 0: y = p.y(row, y_offset)
    return p.Block.match(get_segment(data, p, x, y, MATCH_PIXELS), MATCH_PIXELS)
# fmt: on


def get_segment(data: bytes, p: ParamCls, x: int, y: int, pixels: int = 1) -> bytes:
    d = BPP * (p.GAME_SIZE[0] * y + x)
    return data[d : d + BPP * pixels]


def save_debug(board_data: BoardData) -> None:
    *_, p, y, b = board_data
    serial = "" if b is None else f"_{b.serialize()}"
    draw_debug(board_data).save(f"debug_{p.GAME_SIZE[1]}_{y}{serial}.png")


def draw_debug(board_data: BoardData) -> Image:
    original, data, p, y_offset, _ = board_data
    img = original.copy()
    draw = PIL.ImageDraw.Draw(img)
    draw.rectangle(
        (p.OFFSET[0], p.BLOCKS_Y_RANGE[1], p.OFFSET[0] + p.WIDTH, p.BLOCKS_Y_RANGE[0])
    )
    for row in range(c.BOARD_ROWS):
        if y_offset is None:
            break
        y = p.y(row, y_offset)
        draw.rectangle((p.OFFSET[0], y - 1, p.OFFSET[0] + p.WIDTH, y + 1))
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
            ds = 3
            draw.rectangle((x1, y1, x2, y2), outline=color)
            draw.rectangle((x1 + dx + ds, y1 + dy, x2 - dx, y2 - dy - ds), fill=color)
    return img


def press_key(keyname: str) -> None:
    # pyautogui.press() does not work: no delay between its keyDown and keyUp
    pyautogui.keyDown(keyname)
    pyautogui.keyUp(keyname)


def get_keyname(keycode: t.Union[str, int]) -> str:
    try:
        name = _get_keyname(int(keycode))
    except (ValueError, UnicodeDecodeError):
        raise InvalidValueError("Invalid key code: %s", keycode)
    if name not in pyautogui.KEY_NAMES:
        raise InvalidValueError("Invalid key name: %r, keycode=%r", name, keycode)
    return name


if u.HAVE_PYGAME:
    # Exapunks uses SDL: https://wiki.libsdl.org/SDL2/SDLKeycodeLookup
    def _get_keyname(keycode: int) -> str:
        # "return"->"return", "caps lock"->"capslock", "left ctrl"->"ctrlleft"
        name = u.pygame.key.name(keycode).split(" ", 1)
        if name[-1] in ("ctrl", "shift", "alt"):
            name.reverse()
        return "".join(name)

else:
    _keymap = {0x4000004F + i: n for i, n in enumerate(("right", "left", "down", "up"))}
    _keymap.update(
        {0x400000E0 + i: f"{n}left" for i, n in enumerate(("ctrl", "shift", "alt"))}
    )

    def _get_keyname(keycode: int) -> str:
        return _keymap.get(keycode) or chr(keycode)


def get_screen_size() -> Size:
    return pywinctl.getScreenSize()


def get_parameters(size: Size) -> ParamCls:
    cls = PARAMETERS.get(size)
    if cls is None:
        raise UnsupportedWindowSizeError(
            "Unsupported game window size: %s, must be one of %s",
            size,
            tuple(PARAMETERS.keys()),
        )
    if cls.GAME_SIZE != (0, 0):
        return cls  # class already updated

    # Derived constants
    cls.GAME_SIZE = size
    cls.WIDTH = cls.BLOCK_SIZE[0] * c.BOARD_COLS
    cls.MATCH_X_OFFSET = (cls.BLOCK_SIZE[0] - MATCH_PIXELS) // 2
    cls.BLOCKS_Y_RANGE = (
        cls.OFFSET[1] + cls.BLOCK_SIZE[1] * c.BOARD_ROWS,
        cls.OFFSET[1],
        -1,
    )
    # Wizardry to add default members from the base class in Block enum
    if cls.Block.__members__.keys() != Parameters.Block.__members__.keys():
        members = Parameters.Block.__members__.copy()
        members.update(cls.Block.__members__)
        # Using cls.Block = enum.Enum(...) makes mypy unhappy.
        setattr(cls, "Block", enum.Enum(
            "Block", members, qualname=cls.Block.__qualname__, type=BaseBlock
        ))  # fmt: skip
    return cls


# fmt: off
# Not needed in pywinctl > 0.0.42
def _patch_ewmh() -> None:
    def setactivewindow(self: "EWMH", win: t.Any) -> None:
        self._setProperty("_NET_ACTIVE_WINDOW", [2, 0, win.id], win)
    # noinspection PyProtectedMember
    from pywinctl._pywinctl_linux import EWMH as EWMH
    EWMH.setActiveWindow = types.MethodType(setactivewindow, EWMH)


if u.LINUX:
    import types
    _patch_ewmh()
