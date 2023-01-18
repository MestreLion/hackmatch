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

# Windows
if sys.platform == 'win32':
    SAVE_PATH_PREFIX = "~/Documents/My Games"

# macOS
elif sys.platform == 'darwin':
    SAVE_PATH_PREFIX = "~/Library/Application Support"

# Linux and variants
else:
    SAVE_PATH_PREFIX = os.environ.get("XDG_DATA_HOME") or "~/.local/share"

# Paths
SAVE_PATH_SUFFIX = "EXAPUNKS/{steam_user_id}/config.cfg"
GAME_CONFIG_PATH = ""  # to be determined at run-time by init()

# Steam
STEAM_LAUNCH_URI = "steam://rungameid/716490"
STEAM_USERID_URL = "https://steamcommunity.com/id/{steam_user_name}"

# Graphics
WINDOW_TITLE = "EXAPUNKS"
WINDOW_SIZE = (1920, 1080)

# Game Settings
GameSettings: 't.TypeAlias' = t.Dict[str, t.Union[str, int, bool]]
GAME_SETTINGS: GameSettings = {
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
    "steam_user_id": 0,
}


def init(_args):
    global GAME_CONFIG_PATH
    if not config['steam_user_id']:
        config['steam_user_id'] = get_steam_user_id(config["steam_user_name"])
    GAME_CONFIG_PATH = get_game_config_path(config['steam_user_id'])


def get_steam_user_id(steam_user_name: str) -> int:
    # https://github.com/ValvePython/steam
    # html = requests.get(STEAM_USERID_URL.format(steam_user_name=steam_user_name)).text
    html = steam_user_name
    data = re.search(r"^\s*g_rgProfileData\s*=\s*(?P<json>.*);\s*$", html, re.MULTILINE)
    if not data:
        return 0
    return int(json.loads(data.group('json'))['steamid'])


def get_game_config_path(steam_user_id: int = 0):
    fmt = pathlib.Path(SAVE_PATH_PREFIX, SAVE_PATH_SUFFIX).expanduser()
    path = str(fmt).format(steam_user_id=(steam_user_id or "*"))
    if steam_user_id:
        return path
    try:
        return next(pathlib.Path('/').glob(path[1:]))
    except StopIteration:
        raise FileNotFoundError("Could not find the game config: %s", path)
