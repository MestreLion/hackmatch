# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Game solver
"""

import logging
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


class Move:
    """Logic Move"""


class Board:
    def __init__(
        self,
        grid: t.Optional[Grid] = None,
        phage_col: int = c.BOARD_COLS // 2,
        held_block: Block = EMPTY,
    ):
        self.grid: Grid = grid or {}
        self.phage_col: int = phage_col
        self.held_block: Block = held_block

    def get_block(self, col: int, row: int) -> Block:
        return self.grid.get((col, row), EMPTY)

    def set_block(self, col: int, row: int, block: Block) -> None:
        if not (0 <= col < c.BOARD_COLS and 0 <= row < c.BOARD_ROWS):
            raise InvalidCoordError("Invalid board coordinates: %s", (col, row))
        self.grid[col, row] = block

    def solve(self) -> t.List[Move]:
        return []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (
            self.grid == other.grid
            and self.phage_col == self.phage_col
            and self.held_block == self.held_block
        )

    def __str__(self) -> str:
        return "\n".join(
            "".join(str(self.get_block(col, row)) for col in range(c.BOARD_COLS))
            for row in range(c.BOARD_ROWS)
        )
