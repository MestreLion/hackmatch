# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Configuration, settings and general constants
"""

import argparse
import json
import logging
import os
import pathlib
import re
import typing as t

from . import util as u

if u.WINDOWS:
    SAVE_PATH_PREFIX = u.my_documents_path("My Games")  # by default "~/Documents/My Games"

elif u.MACOS:
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
GameSettings: u.TypeAlias = t.Dict[str, t.Union[str, int, bool]]
GAME_SETTINGS: GameSettings = {
    # "Resolution.Width": WINDOW_SIZE[0],
    # "Resolution.Height": WINDOW_SIZE[1],
    "EnableCrtDistortion": False,
}

# Game logic
BOARD_COLS = 7
BOARD_ROWS = 9

# Misc
COPYRIGHT = """
Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
"""

INITIALIZED = False  # Indicates if init() has been called

config: t.Dict[str, t.Any] = {
    "bot_fps": 20,
    "game_launch_timeout": 60,
    "steam_user_name": "",
    "steam_user_id": 0,
}

args: argparse.Namespace = argparse.Namespace(
    benchmark=False,
    debug=False,
    loglevel=logging.INFO,
    path=None,
    string=None,
    timeout=850,
    watch=False,
)

log = logging.getLogger(__name__)


def init(parsed_args: t.Optional[argparse.Namespace] = None) -> None:
    global args, GAME_CONFIG_PATH, INITIALIZED
    if parsed_args is not None:
        args = parsed_args
    if not config["steam_user_id"]:
        config["steam_user_id"] = get_steam_user_id(config["steam_user_name"])
    GAME_CONFIG_PATH = get_game_config_path(config["steam_user_id"])
    INITIALIZED = True


def check_init() -> bool:
    if INITIALIZED:
        return True
    log.warning(
        "Application not initialized, using default settings."
        " Run %s.init() to avoid this.",
        __name__,
    )
    init()
    return False


def get_steam_user_id(steam_user_name: str) -> int:
    # https://github.com/ValvePython/steam
    # html = requests.get(STEAM_USERID_URL.format(steam_user_name=steam_user_name)).text
    html = steam_user_name
    data = re.search(r"^\s*g_rgProfileData\s*=\s*(?P<json>.*);\s*$", html, re.MULTILINE)
    if not data:
        return 0
    return int(json.loads(data.group("json"))["steamid"])


def get_game_config_path(steam_user_id: int = 0) -> str:
    fmt = pathlib.Path(SAVE_PATH_PREFIX, SAVE_PATH_SUFFIX).expanduser()
    path = str(fmt).format(steam_user_id=(steam_user_id or "*"))
    if steam_user_id:
        return path
    try:
        return str(next(pathlib.Path("/").glob(path[1:])))
    except StopIteration:
        raise u.FileOpenError("Could not find the game config folder: %s", path)
