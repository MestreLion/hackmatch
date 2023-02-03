# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
High-level bot logic
"""

import logging
import time
import typing as t

from . import ai
from . import config as c
from . import game
from . import util as u
from . import gui

log = logging.getLogger(__name__)


def bot() -> None:
    window: t.Optional[gui.GameWindow]
    settings: c.GameSettings = game.read_settings()
    if not game.check_settings(settings):
        window = get_game_window(launch=False, activate=False)
        if window is not None:
            window.close()
            time.sleep(1)  # so arbitrary!
        game.change_settings()

    window = get_game_window(activate=(c.args.path is None))
    assert window is not None
    log.info("Game window: %s", window)

    while True:
        board: ai.Board = window.new_board()
        log.info("Board:\n%s", board)
        moves = board.solve()
        if moves:
            log.info("Moves: %s", moves)
        window.apply_moves(moves)
        if c.args.path:
            break


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
        time.sleep(1)
