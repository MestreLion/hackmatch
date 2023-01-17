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
from . import util as u
from . import gui

log = logging.getLogger(__name__)


def bot():
    window: gui.GameWindow = get_game_window()
    log.info("Game window: %s", window)
    if not check_settings(window):
        window.close()
        time.sleep(1) # so arbitrary!
        change_settings()
        window = get_game_window()
        check_settings(window, raise_on_error=True)

    board = ai.Board.from_image(window.take_screenshot())
    board.solve()


def get_game_window() -> gui.GameWindow:
    launch_timer: t.Optional[u.Timer] = None
    while True:
        try:
            window = gui.GameWindow.find_by_title(c.WINDOW_TITLE)
        except gui.WindowNotFoundError:
            pass
        except u.HMError as e:
            log.error(e)
        else:
            return window
        if not launch_timer:
            launch_game()
            launch_timer = u.Timer(c.config['game_launch_timeout'])
            log.info("Game launched, waiting %s seconds for game window",
                     c.config['game_launch_timeout'])
        elif launch_timer.expired:
            raise u.HMError("Game did not start after %s seconds",
                            c.config['game_launch_timeout'])
        time.sleep(1)


def check_settings(window, raise_on_error=False):
    ok = window.size[0] == c.WINDOW_SIZE[0]
    if not ok:
        if raise_on_error:
            raise u.HMError("Incorrect game settings")
        log.warning("Incorrect game settings: game width is %s, expected %s",
                    window.size[0], c.WINDOW_SIZE[0])
    return ok


def launch_game():
    try:
        u.open_file(c.STEAM_LAUNCH_URI)
    except u.HMError as e:
        raise u.HMError("Could not launch the game: %s", e)


def change_settings():
    path = c.get_game_config_path()
    log.debug("Game config path: %s", path)
    with open(path) as f:
        settings = f.readlines()
    data = {k.strip(): v.strip() for k, v in (line.split('=') for line in settings)}
    log.debug("Parsed game settings: %s", data)
    data.update(c.GAME_SETTINGS)
    text = "\n".join(f"{k} = {v}" for k, v in data.items())
    log.debug("Updated game settings: \n%s", text)
    with open(path, 'w') as f:
        f.write(text + '\n')
