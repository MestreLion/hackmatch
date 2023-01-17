# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Configuration, settings and constants
"""

import json
import logging
import os
import pathlib
import re
import sys
import typing as t

# Paths
if sys.platform == "win32":
    SAVE_PREFIX = "~/Documents/My Games"
elif sys.platform == "darwin":
    SAVE_PREFIX = "~/Library/Application Support"
else:  # linux
    SAVE_PREFIX = os.environ.get("XDG_DATA_HOME") or "~/.local/share"

GAME_CONFIG_FMT = str(pathlib.Path(SAVE_PREFIX,
                                   "EXAPUNKS/{steam_user_id}/config.cfg").expanduser())

# Steam
STEAM_LAUNCH_URI = "steam://rungameid/716490"
STEAM_USERID_URL = "https://steamcommunity.com/id/{steam_user_name}"

# Graphics
WINDOW_TITLE = "EXAPUNKS"
WINDOW_SIZE = (1920, 1080)

# Game Settings
GAME_SETTINGS = {
    'Resolution.Width': WINDOW_SIZE[0],
    'Resolution.Height': WINDOW_SIZE[1],
    'EnableCrtDistortion': False,
}

# Game logic
BOARD_COLS = 7
BOARD_ROWS = 9

# Misc
COPYRIGHT = """
Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
"""

log = logging.getLogger(__name__)

config: t.Dict[str, t.Any] = {
    "game_launch_timeout": 60,
    "steam_user_name": "",
}


def get_steam_user_id(steam_user_name: str) -> int:
    # https://github.com/ValvePython/steam
    # html = requests.get(STEAM_USERID_URL.format(steam_user_name=steam_user_name)).text
    html = steam_user_name
    data = re.search(r"^\s*g_rgProfileData\s*=\s*(?P<json>.*);\s*$", html, re.MULTILINE)
    if not data:
        return 0
    return int(json.loads(data.group('json'))['steamid'])


def get_game_config_path():
    user_id = get_steam_user_id(config["steam_user_name"])
    path = GAME_CONFIG_FMT.format(steam_user_id=(user_id or "*"))
    if user_id:
        return path
    try:
        return next(pathlib.Path('/').glob(path[1:]))
    except StopIteration:
        raise FileNotFoundError("Could not find the game config file: %s", path)
