# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Game solver
"""
import enum
import logging
import random
import typing as t

from . import config as c
from . import util as u

log = logging.getLogger(__name__)


# Ugly hack, for now...
Block: u.TypeAlias = str
EMPTY = "."
Grid: u.TypeAlias = t.Dict[t.Tuple[int, int], Block]


class InvalidCoordError(u.HMError, ValueError):
    """The specified row or column for a block in the board is invalid"""


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


class Board:
    def __init__(
        self,
        grid: t.Optional[Grid] = None,
        phage_col: t.Optional[int] = None,
        held_block: Block = EMPTY,
    ):
        self.grid: Grid = {} if grid is None else grid
        self.phage_col: int = c.BOARD_COLS // 2 if phage_col is None else phage_col
        self.held_block: Block = held_block

    def get_block(self, col: int, row: int) -> Block:
        return self.grid.get((col, row), EMPTY)

    def set_block(self, col: int, row: int, block: Block) -> None:
        if not (0 <= col < c.BOARD_COLS and 0 <= row < c.BOARD_ROWS):
            raise InvalidCoordError("Invalid board coordinates: %s", (col, row))
        self.grid[col, row] = block

    def serialize(self) -> str:
        return str(self).replace("\n", "-")

    def solve(self) -> t.List[Move]:
        return find_match(self)

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
        phage_row[self.phage_col] = "@" if self.held_block is EMPTY else self.held_block
        return (
            "\n".join(
                "".join(str(self.get_block(col, row)) for col in range(c.BOARD_COLS))
                for row in range(c.BOARD_ROWS)
            )
            + "\n"
            + "".join(phage_row)
        )


def find_match(board: Board) -> t.List[Move]:
    # Laelath:
    # Check if initial board has match, return no moves
    # For each board popped from a deque, starting with initial
    # get a new board for each possible movement, append move to board moves list
    # if new board was already seen: ignore it
    # if new board has match: return its moves
    # Add board to seen list
    # Calculate its score. If max, save moves and score
    # push each new board to deque
    # repeat until timeout or deque empty
    # return highest score moves
    # Scoring: sum of squared block group sizes, minus imbalance squared, +1 if holding
    # Imbalance: sum of squared differences from each column height to the mean height

    # Such an impressive AI!
    moves = []
    while len(moves) < 30:
        moves.extend([Move.SWAP, Move.GRAB])
        moves.extend(
            [random.choice((Move.LEFT, Move.RIGHT))] * random.randint(1, c.BOARD_COLS // 2)
        )
    return moves
