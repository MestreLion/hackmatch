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
# Silence PIL debug messages when saving PNGs
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

_BT = t.TypeVar("_BT", bound="BaseBlock")
BBox: u.TypeAlias = t.Tuple[int, int, int, int]  # left, top, right, bottom
Size: u.TypeAlias = t.Tuple[int, int]  # width, height
Offset: u.TypeAlias = t.Tuple[int, int]  # x, y
Image: u.TypeAlias = PIL.Image.Image
Window: u.TypeAlias = pywinctl.Window
ParamCls: u.TypeAlias = t.Type["Parameters"]

BPP: int = 3  # Bits per pixel in Image data (bit depth)
MATCH_PIXELS = 8  # Pixels in a row to consider a block match
PHAGE_CROUCH = (-3, 3)  # Phage extra offset when crouching. X for silver, Y for held

# Delay after each key event (Down and Up), in seconds. Full key press = 2 * PAUSE
# Laelath: KEY_DELAY=17ms; PyAutoGUI default = 0.1 = 100ms = 10 FPS
KEY_DELAY = 0.017  # 17ms ~= 60 FPS


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
    MATCH_Y_OFFSET: int = 0  # Offset from block top to match marker. Cosmetic, for debug
    HELD_Y_OFFSET: int = 0  # Y offset from board top to phage held block marker
    PHAGE_SILVER_OFFSET: Offset = (0, 0)  # From (column left, board top) to phage marker
    PHAGE_SILVER_DATA: bytes = b""
    PHAGE_PINK_OFFSET: Offset = (0, 0)  # From (column left, board top) to phage marker
    PHAGE_PINK_DATA: bytes = b""
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
    def x_offset(cls, col: int, x_offset: int) -> int:
        if not 0 <= col < c.BOARD_COLS:
            raise InvalidValueError("Invalid column: %s", col)
        if not 0 <= x_offset < cls.BLOCK_SIZE[0]:
            raise InvalidValueError("Invalid x offset: %s", x_offset)
        return cls.OFFSET[0] + col * cls.BLOCK_SIZE[0] + x_offset

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
    # Same positions as Laelath
    BLOCK_SIZE = (72, 72)
    OFFSET = (440, 151)
    HEIGHT = 770  # Laelath: 810
    MATCH_Y_OFFSET = 56
    HELD_Y_OFFSET = 757  # 908 - OFFSET[1]
    PHAGE_SILVER_OFFSET = (22, 682)  # (22, 833 - OFFSET[1])
    PHAGE_SILVER_DATA = 2 * b"\xe4\xff\xff" + 4 * b"\xe5\xff\xff" + 2 * b"\xe4\xff\xff"
    PHAGE_PINK_OFFSET = (0, 0)
    PHAGE_PINK_DATA = b""


class Parameters1920x1200(Parameters1920x1080):
    OFFSET = (440, 211)
    _silver_data = (2 * b"\xe1\xfd\xff", b"\xe2\xfd\xff", b"\xe3\xfe\xff")
    PHAGE_SILVER_DATA = b"".join(_silver_data) + b"".join(reversed(_silver_data))

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
    # Same positions as fidel-solver
    BLOCK_SIZE = (60, 60)
    OFFSET = (367, 126)
    HEIGHT = 643
    MATCH_Y_OFFSET = 46
    HELD_Y_OFFSET = 630
    PHAGE_SILVER_OFFSET = (19, 568)  # fidel-solver: (18, 694 - OFFSET[1])
    PHAGE_SILVER_DATA = 1 * b"\xe4\xff\xff" + 3 * b"\xe5\xff\xff" + b"\xe4\xff\xff"

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
        # Configure PyAutoGUI
        pyautogui.PAUSE = KEY_DELAY
        pyautogui.FAILSAFE = False

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

    def new_board(self, debug: bool = False) -> ai.Board:
        # Screenshot takes ~10ms. Laelath: RECHECK_WAIT_TIME = KEY_DELAY + 3 = 20ms
        fps = 40  # 25ms
        clock = u.FrameRateLimiter(fps)
        error_count = 0
        while True:
            image: Image = self.take_screenshot()
            size = image.size
            if size != self.prev_size:
                log.info("Game window resized: %s", size)
                self.prev_size = size
            try:
                *_, board = board_data = parse_image(image)
            except UnsupportedWindowSizeError as e:
                # warn every 2 seconds, raise after 10
                if error_count >= 10 * fps:
                    raise
                if error_count % (2 * fps) == 0:
                    log.warning(e)
                error_count += 1
                clock.wait()
                continue
            if board is not None and board != self.prev_board:
                if debug:
                    save_debug(board_data)
                self.prev_board = board
                return board
            clock.wait()

    def send_moves(self, moves: t.List[ai.Move]) -> None:
        for move in moves:
            press_key(self.keymap[move])


def get_board_from_path(path: str, debug: bool = False) -> t.Optional[ai.Board]:
    if not path:
        raise u.FileOpenError("Invalid empty image path")
    image: Image = PIL.Image.open(path).convert(mode="RGB")
    board_data = parse_image(image)
    if debug:
        save_debug(board_data, save_original=False)
    return board_data.board


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

    # TODO: Optimization: loop col->row, top to phage, break col when EMPTY
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
    y = p.OFFSET[1] + p.PHAGE_SILVER_OFFSET[1]
    w = len(p.PHAGE_SILVER_DATA) // BPP
    for col in range(c.BOARD_COLS):
        x = p.x_offset(col, p.PHAGE_SILVER_OFFSET[0])
        for off in (0, PHAGE_CROUCH[0]):  # normal / crouch
            if w and get_segment(data, p, x + off, y, w) == p.PHAGE_SILVER_DATA:
                return col
    else:
        return None


def find_held_block(data: bytes, p: ParamCls, col: t.Optional[int]) -> Parameters.Block:
    # TODO: It's not that simple... but who needs find_pink()?
    if col is None:
        return p.Block.EMPTY
    x = p.x(col)
    for off in (0, PHAGE_CROUCH[1]):
        block = get_block_at(data, p, x=x, y=p.OFFSET[1] + p.HELD_Y_OFFSET + off)
        if block != p.Block.EMPTY:
            return block
    else:
        return p.Block.EMPTY


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


def save_debug(board_data: BoardData, save_original: bool = True) -> None:
    image, _, p, y_offset, board = board_data
    y = "" if y_offset is None else f"_{y_offset}"
    serial = "" if board is None else f"_{board.serialize()}"
    if save_original:
        image.save(f"board_{p.GAME_SIZE[1]}{y}{serial}.png")
    draw_debug(board_data).save(f"debug_{p.GAME_SIZE[1]}{y}{serial}.png")


def draw_debug(board_data: BoardData) -> Image:
    original, data, p, y_offset, _ = board_data
    img = original.copy()
    draw = PIL.ImageDraw.Draw(img)

    def draw_board_rect(y1: int, y2: int) -> None:
        draw.rectangle((p.OFFSET[0], y1, p.OFFSET[0] + p.WIDTH, y2))

    def draw_block(x0: int, y0: int) -> None:
        # Block match segment
        draw.rectangle((x0 - 1, y0 - 1, x0 + MATCH_PIXELS, y0 + 1))
        block = get_block_at(data, p, x=x0, y=y0)
        if block == p.Block.EMPTY:
            return
        # Block outline and center full square
        color = t.cast(t.Tuple[int, int, int], tuple(block.value[:3]))
        width, height = p.BLOCK_SIZE
        x1, y1 = x0 - p.MATCH_X_OFFSET, y0 - p.MATCH_Y_OFFSET
        x2, y2 = x1 + width - 1, y1 + height - 1
        dx, dy = width // 4, height // 4
        ds = 2
        draw.rectangle((x1, y1, x2, y2), outline=color)
        draw.rectangle((x1 + dx + ds, y1 + dy - ds, x2 - dx - ds, y2 - dy - ds), fill=color)

    def draw_phage_column(phage: int, y0: int, width: int, black: bool = False) -> None:
        x0 = p.x_offset(phage, p.PHAGE_SILVER_OFFSET[0])
        x1 = x0 + min(0, PHAGE_CROUCH[0]) - 1
        x2 = x0 + max(0, PHAGE_CROUCH[0]) + width
        draw.rectangle((x1, y0 - 1, x2, y0 + 1), outline=(0, 0, 0) if black else None)

    # Blocks area
    draw_board_rect(p.BLOCKS_Y_RANGE[1], p.BLOCKS_Y_RANGE[0])

    # Blocks
    for row in range(c.BOARD_ROWS):
        if y_offset is None:
            break
        y = p.y(row, y_offset)
        # y_offset
        draw_board_rect(y - 1, y + 1)
        for col in range(c.BOARD_COLS):
            x = p.x(col)
            draw_block(x, y)

    # Phage column
    w = len(p.PHAGE_SILVER_DATA) // BPP
    y = p.OFFSET[1] + p.PHAGE_SILVER_OFFSET[1]
    # All columns, in white
    draw_board_rect(y - 1, y + 1)
    for col in range(c.BOARD_COLS):
        draw_phage_column(col, y, w)
    # Matched column, if found, in black
    phage_col = find_phage_column(data, p)
    if phage_col is not None:
        draw_phage_column(phage_col, y, w, black=True)

    # Phage held
    y = p.OFFSET[1] + p.HELD_Y_OFFSET
    ya = y + min(0, PHAGE_CROUCH[1]) - 1
    yb = y + max(0, PHAGE_CROUCH[1]) + 1
    draw_board_rect(ya, yb)
    if phage_col is not None:
        x = p.x(phage_col)
        for off in (0, PHAGE_CROUCH[1]):
            draw_block(x, y + off)

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
    if cls.GAME_SIZE == size:
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
    # Wizardry to merge Block enum members with default ones from Parameters.BLock
    # Note: this merges with "root" class Parameters.BLock *only*, not with other
    # (intermediary) parent bases, if any.
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
