# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Game solver

Solving algorithm taken from Justin Frank
https://github.com/laelath/hack-match-bot
"""
# TODO: Optimizations:
# - Board._column_heights cache, cloned, updated on Board.move() only when SWAP, GRAB
# - Board._score cache, cloned, reset on Board.move() only when SWAP, GRAB
# - multiprocessing.Pool() or concurrent.futures.ProcessPoolExecutor() in solve()
#   4 workers to parallelize only the Move loop, returning board/None and best/None
#   so the main process adds to queue and update boards list and best.

import collections
import enum
import logging
import random
import typing as t

from . import config as c
from . import util as u

# Laelath: MAX_SEARCH_TIME = 110ms
MAX_SOLVE_TIME = 850  # ~50 frames @ 60 FPS

Coord: u.TypeAlias = t.Tuple[int, int]
Grid: u.TypeAlias = t.Dict[Coord, "Block"]

log = logging.getLogger(__name__)


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
        return 2 if self.name[-5:] == "_BOMB" else 4


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

    def __str__(self) -> str:
        return self.name


class Group(t.NamedTuple):
    block: Block
    coords: t.List[Coord]


class Candidate(t.NamedTuple):
    board: "Board"
    score: float
    has_match: bool = False


class Board:
    def __init__(
        self,
        grid: t.Optional[Grid] = None,
        phage_col: t.Optional[int] = None,
        held_block: Block = Block.EMPTY,
        moves: t.Optional[t.List[Move]] = None,
        _groups: t.Optional[t.List[Group]] = None,
    ):
        self.grid: Grid = {} if grid is None else grid
        self.phage_col: int = c.BOARD_COLS // 2 if phage_col is None else phage_col
        self.held_block: Block = held_block
        self._moves: t.List[Move] = [] if moves is None else moves
        self._groups: t.List[Group] = [] if _groups is None else _groups
        # self._score: int = 0

    @property
    def moves(self) -> t.List[Move]:
        return self._moves

    @classmethod
    def from_string(
        cls, text: str, sep: str = "-", phage: str = "@", empty: str = ".", ground: str = "_"
    ) -> "Board":
        # TODO: perhaps use u.chunked() to simplify this
        self = cls()
        lines = text.replace(sep, "\n").splitlines()
        if not lines:
            return self

        assert len(lines) <= c.BOARD_ROWS + 1
        for row, line in enumerate(lines[:-1]):
            assert not line or len(line) == c.BOARD_COLS
            for col, char in enumerate(line):
                if char != empty:
                    self.set_block(col, row, Block(char))
        line = lines[-1]
        assert len(line) <= c.BOARD_COLS
        for col, char in enumerate(lines[-1]):
            if char == ground:
                continue
            if char != phage:
                self.held_block = Block(char)
            self.phage_col = col
            break
        return self

    def get_block(self, col: int, row: int) -> Block:
        return self.grid.get((col, row), Block.EMPTY)

    def set_block(self, col: int, row: int, block: Block) -> None:
        if not (0 <= col < c.BOARD_COLS and 0 <= row < c.BOARD_ROWS):
            raise InvalidCoordError("Invalid board coordinates: %s", (col, row))
        # For correctness this should also reset _groups cache.
        # Ignoring for performance as this is only called when parsing from image
        # (when cache is not used) and from move(), which performs the reset itself.
        self.grid[col, row] = block

    def clone(self) -> "Board":
        return self.__class__(
            self.grid.copy(),
            self.phage_col,
            self.held_block,
            self.moves.copy(),
            self._groups.copy(),
        )

    def lowest_block(self, col: int, up_to: int = 0) -> t.Tuple[int, Block]:
        for row in range(c.BOARD_ROWS - 1, up_to - 1, -1):
            block = self.get_block(col, row)
            if block:
                return row, block
        else:
            return -1, Block.EMPTY

    def move(self, move: Move) -> None:
        self._moves.append(move)
        col = self.phage_col
        if move == Move.LEFT:
            if col > 0:
                self.phage_col -= 1
        elif move == Move.RIGHT:
            if col < c.BOARD_COLS - 1:
                self.phage_col += 1
        elif move == Move.SWAP:
            row, block = self.lowest_block(col, 1)
            if row > 0:
                self.set_block(col, row, self.get_block(col, row - 1))
                self.set_block(col, row - 1, block)
                self._groups = []  # invalidate cache
        else:  # Exchange: move.GRAB/THROW
            row, block = self.lowest_block(col)
            if self.held_block:
                # Throw: lowest block must not be at the lowest row
                if row < c.BOARD_ROWS - 1:
                    self.set_block(col, row + 1, self.held_block)
                    self.held_block = Block.EMPTY
                    self._groups = []  # invalidate cache
            else:
                # Grab: There must be a (non-empty) block in the column
                if block:
                    self.set_block(col, row, self.held_block)
                    self.held_block = block
                    self._groups = []  # invalidate cache

    def __eq__(self, other: object) -> bool:
        """Equivalence when parsing blocks from image, ignores phage column and moves"""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.grid == other.grid and self.held_block == self.held_block

    def __hash__(self) -> int:
        """Identity when solving the board, ignores moves list"""
        return hash(
            (
                tuple((coord, block) for (coord, block) in self.grid.items() if block),
                self.phage_col,
                self.held_block,
            )
        )

    def __str__(self) -> str:
        return self.serialize(sep="\n")

    def serialize(
        self, sep: str = "-", phage: str = "@", empty: str = ".", ground: str = "_"
    ) -> str:
        phage_row = [ground] * c.BOARD_COLS
        phage_row[self.phage_col] = str(self.held_block) if self.held_block else phage
        return (
            sep.join(
                "".join(str(self.get_block(col, row) or empty) for col in range(c.BOARD_COLS))
                for row in range(c.BOARD_ROWS)
            )
            + sep
            + "".join(phage_row)
        )

    @staticmethod
    def adjacents(col: int, row: int) -> t.List[Coord]:
        coords: t.List[Coord] = []
        for offset in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            coord = (col + offset[0], row + offset[1])
            if 0 <= coord[0] < c.BOARD_COLS and 0 <= coord[1] < c.BOARD_ROWS:
                coords.append(coord)
        return coords

    def solve(self, max_solve_time: int = MAX_SOLVE_TIME) -> t.List[Move]:
        return solve(self, max_solve_time)

    def heights(self) -> t.List[int]:
        return list(
            sum(1 if self.get_block(col, row) else 0 for row in range(c.BOARD_ROWS))
            for col in range(c.BOARD_COLS)
        )

    def groups(self) -> t.List[Group]:
        if self._groups:
            return self._groups

        def invite(coord: Coord, group: Group) -> None:
            block = self.get_block(*coord)
            if block and coord not in grouped and block == group.block:
                grouped.add(coord)
                if not group.coords:
                    self._groups.append(group)
                group.coords.append(coord)
                for adjacent in self.adjacents(*coord):
                    invite(adjacent, group)

        grouped: t.Set[Coord] = set()
        for col in range(c.BOARD_COLS):
            for row in range(c.BOARD_ROWS):
                invite((col, row), Group(self.get_block(col, row), []))
        return self._groups

    def has_match(self) -> bool:
        return any(len(group.coords) >= group.block.match_size() for group in self.groups())

    def score(self) -> float:
        """Sum of squared block group sizes, minus imbalance squared, +1 if holding"""
        groups = self.groups()
        return (
            sum(len(group.coords) ** 2 for group in groups) / (len(groups) if groups else 1)
            - self.imbalance() ** 2
            + (1 if self.held_block else 0)
        )

    def imbalance(self) -> float:
        """Sum of squared differences from each column height to the mean height"""
        heights = self.heights()
        mean = sum(heights) / len(heights)
        return sum((height - mean) ** 2 for height in heights)  # + max(heights)

    def debug(self, caption: str = "Board", show_self: bool = True) -> None:
        if not log.level <= logging.DEBUG:
            return
        if show_self:
            log.debug("%s:\n%s", caption, self)
        log.debug("Groups: %s", self.groups())
        log.debug("Heights: %s", self.heights())
        log.debug("Imbalance: %s", self.imbalance())
        log.debug("Score: %s", self.score())
        log.debug("Has match? %s", self.has_match())
        log.debug("Moves (%s): %s", len(self.moves), self.moves)


def solve(board: Board, max_solve_time: int = MAX_SOLVE_TIME) -> t.List[Move]:
    board.debug(show_self=False)
    boards: t.Set[Board] = {board}
    best = Candidate(board=board, score=board.score(), has_match=board.has_match())
    queue: t.Deque[Board] = collections.deque([board])  # First in, first out
    timer = u.Timer(max_solve_time / 1000) if max_solve_time > 0 else u.Clock()
    steps = 0
    while queue and not timer.expired and not best.has_match:
        parent = queue.popleft()
        length = len(parent.moves)
        if steps < length + 1:
            steps = length + 1
        # Get a new board for each possible movement
        for move in Move:
            board = parent.clone()
            board.move(move)
            if board in boards:
                # Ignore duplicated boards
                continue
            if board.has_match():
                best = Candidate(board=board, score=0, has_match=True)
                break
            boards.add(board)
            score = board.score()
            if score > best.score:
                best = Candidate(board=board, score=score)
            queue.append(board)
    elapsed = timer.elapsed
    if best.has_match:
        reason = "MATCH FOUND! After"
    elif queue:
        reason = "TIMEOUT after"
    else:
        reason = "Completed after"
    log.info(
        "%s %.0fms, %s boards (%.0f boards/s), %s moves deep",
        reason,
        elapsed * 1000,
        len(boards),
        len(boards) / elapsed,
        steps,
    )
    best.board.debug("New board")
    # Move to the middle column to help next solve() to see more boards
    center = best.board.phage_col - (c.BOARD_COLS // 2)
    if center:
        best.board.moves.extend(abs(center) * ([Move.LEFT] if center > 0 else [Move.RIGHT]))
    return best.board.moves  # or deep_blue(board)


# noinspection PyUnusedLocal
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
