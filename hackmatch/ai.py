# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Game solver

Solving algorithm taken from Justin Frank
https://github.com/laelath/hack-match-bot
"""
import collections
import enum
import logging
import random
import typing as t

from . import config as c
from . import util as u

log = logging.getLogger(__name__)


Coord: u.TypeAlias = t.Tuple[int, int]
Grid: u.TypeAlias = t.Dict[Coord, "Block"]


class InvalidCoordError(u.HMError, ValueError):
    """The specified row or column for a block in the board is invalid"""


class Block(str, enum.Enum):
    # str base so EMPTY can be Falsy, values are otherwise irrelevant
    # So chosen as their str representation for convenience
    EMPTY = ""
    YELLOW = "y"
    GREEN = "g"
    RED = "r"
    PINK = "p"
    BLUE = "b"
    Y_BOMB = "Y"
    G_BOMB = "G"
    R_BOMB = "R"
    P_BOMB = "P"
    B_BOMB = "B"

    def __str__(self) -> str:
        return self.value if self else "."

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self.name}>"

    def match_size(self) -> int:
        return 2 if self.name[:-5] == "_BOMB" else 4


class Move(enum.Enum):
    """Logic Move"""

    # fmt: off
    LEFT  = "KeyMapping.Left"
    RIGHT = "KeyMapping.Right"
#   START = "KeyMapping.Start"
    GRAB  = "KeyMapping.X"
    THROW = "KeyMapping.X"
    SWAP  = "KeyMapping.Y"
    # fmt: on

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self.name}>"


class Group(t.NamedTuple):
    block: Block
    coords: t.List[Coord]


class Path(t.NamedTuple):
    moves: t.List[Move]
    score: int


class Board:
    def __init__(
        self,
        grid: t.Optional[Grid] = None,
        phage_col: t.Optional[int] = None,
        held_block: Block = Block.EMPTY,
        moves: t.Optional[t.List[Move]] = None,
    ):
        self.grid: Grid = {} if grid is None else grid
        self.phage_col: int = c.BOARD_COLS // 2 if phage_col is None else phage_col
        self.held_block: Block = held_block
        self.moves: t.List[Move] = [] if moves is None else moves
        self._groups: t.List[Group] = []
        # self._score: int = 0

    def get_block(self, col: int, row: int) -> Block:
        return self.grid.get((col, row), Block.EMPTY)

    def set_block(self, col: int, row: int, block: Block) -> None:
        if not (0 <= col < c.BOARD_COLS and 0 <= row < c.BOARD_ROWS):
            raise InvalidCoordError("Invalid board coordinates: %s", (col, row))
        self.grid[col, row] = block

    def clone(self) -> "Board":
        return self.__class__(
            self.grid.copy(),
            self.phage_col,
            self.held_block,
            self.moves.copy(),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (
            # Phage column does not matter
            self.grid == other.grid
            and self.held_block == self.held_block
        )

    def __str__(self) -> str:
        phage_row = ["_"] * c.BOARD_COLS
        phage_row[self.phage_col] = str(self.held_block) if self.held_block else "@"
        return (
            "\n".join(
                "".join(str(self.get_block(col, row)) for col in range(c.BOARD_COLS))
                for row in range(c.BOARD_ROWS)
            )
            + "\n"
            + "".join(phage_row)
        )

    def serialize(self) -> str:
        return str(self).replace("\n", "-")

    @staticmethod
    def adjacents(col: int, row: int) -> t.List[Coord]:
        coords: t.List[Coord] = []
        for offset in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            coord = (col + offset[0], row + offset[1])
            if 0 <= coord[0] < c.BOARD_COLS and 0 <= coord[1] < c.BOARD_ROWS:
                coords.append(coord)
        return coords

    def solve(self) -> t.List[Move]:
        return solve(self)

    def groups(self) -> t.List[Group]:
        def invite(coord: Coord, group: Group) -> None:
            block = self.get_block(*coord)
            if block and coord not in grouped and block == group.block:
                grouped.add(coord)
                if not group.coords:
                    self._groups.append(group)
                group.coords.append(coord)
                for adjacent in self.adjacents(*coord):
                    invite(adjacent, group)

        if self._groups:
            return self._groups
        grouped: t.Set[Coord] = set()
        for col in range(c.BOARD_COLS):
            for row in range(c.BOARD_ROWS):
                invite((col, row), Group(self.get_block(col, row), []))
        log.debug(
            "Groups:\n\t%s",
            "\n\t".join(f"{group.block!r}: {group.coords}" for group in self._groups),
        )
        return self._groups

    def has_match(self) -> bool:
        return any(len(group.coords) >= group.block.match_size() for group in self.groups())

    def score(self) -> float:
        """Sum of squared block group sizes, minus imbalance squared, +1 if holding"""
        return (
            sum(len(group.coords) ** 2 for group in self.groups())
            - self.imbalance() ** 2
            + (1 if self.held_block else 0)
        )

    def imbalance(self) -> float:
        """Sum of squared differences from each column height to the mean height"""
        heights: t.List[int] = [
            sum(1 if self.get_block(col, row) else 0 for row in range(c.BOARD_ROWS))
            for col in range(c.BOARD_COLS)
        ]
        mean = sum(heights) / len(heights)
        return sum((heights[col] - mean) ** 2 for col in heights)


def solve(board: Board) -> t.List[Move]:
    if board.has_match():
        return []
    best = Path(moves=[], score=0)
    queue = collections.deque([board])
    # get a new board for each possible movement, append move to board moves list
    # if new board was already seen: ignore it
    # if new board has match: return its moves
    # Add board to seen list
    # Calculate its score. If max, save moves and score
    # push each new board to deque
    # repeat until timeout or deque empty
    # return highest score moves
    if best.moves:
        return best.moves
    return deep_blue(board)


def deep_blue(board: Board) -> t.List[Move]:
    """An impressive, modern AI capable of scoring up to 10,000!"""
    moves: t.List[Move] = []
    while len(moves) < 10:
        moves.extend(random.choice(([Move.SWAP],) + 3 * ([Move.SWAP, Move.GRAB],)))
        moves.extend(
            [random.choice((Move.LEFT, Move.RIGHT))]
            * random.randint(0, (c.BOARD_COLS // 2) + 1)
        )
    return moves
