# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
High-level bot logic
"""

import logging
import typing as t

from . import config as c
from . import game
from . import util as u
from . import gui

log = logging.getLogger(__name__)


def bot() -> None:
    if c.args.path:
        board = gui.get_board_from_path(c.args.path, c.args.debug)
        if board is None:
            return
        log.info("Board:\n%s", board)
        moves = board.solve()
        if moves:
            log.info("Moves: %s", moves)
        return

    validate_game_settings()
    window = get_game_window(activate=(c.args.path is None))
    assert window is not None
    log.info("Game window: %s", window)

    if c.args.benchmark:

        def keep_running() -> bool:
            return not timer.expired

        timer = u.Timer(60)
    else:

        def keep_running() -> bool:
            return True

    while keep_running():
        board = window.new_board()
        log.info("Board:\n%s", board)
        moves = board.solve()
        if moves:
            log.info("Moves: %s", moves)
        if not c.args.watch:
            window.send_moves(moves)
        # Laelath: SOLVE_WAIT_TIME = 4 * KEY_DELAY + 12ms = 80ms. Arbitrary?
        u.Timer(4 * gui.KEY_DELAY + 0.012).wait()


def get_game_window(launch: bool = True, activate: bool = True) -> t.Optional[gui.GameWindow]:
    """Get the game window, launching it if needed"""
    launched: t.Optional[u.Timer] = None
    while True:
        try:
            window = gui.GameWindow.find_by_title(c.WINDOW_TITLE)
        except gui.WindowNotFoundError:
            if not launch:
                return None
        else:
            if activate:
                window.activate(reposition=bool(launched))
            return window
        if not launched:
            launched = u.Timer(c.config["game_launch_timeout"])
            log.info(
                "Launching game and waiting %s seconds for game window",
                c.config["game_launch_timeout"],
            )
            game.launch()
        elif launched.expired:
            raise u.HMError(
                "Game did not start after %s seconds", c.config["game_launch_timeout"]
            )
        u.Timer(1).wait()  # Also arbitrary


def validate_game_settings() -> None:
    settings: c.GameSettings = game.read_settings()
    if not game.check_settings(settings):
        window = get_game_window(launch=False, activate=False)
        if window is not None:
            window.close()
            u.Timer(1).wait()  # so arbitrary!
        game.change_settings()
