# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Steam game launch and settings
"""

import logging
import typing as t

from . import config as c
from . import util as u

RawSettings: u.TypeAlias = t.Dict[str, str]

log = logging.getLogger(__name__)


def launch() -> None:
    log.info("Launch game by Steam URI: %s", c.STEAM_LAUNCH_URI)
    try:
        u.run_file(c.STEAM_LAUNCH_URI)
    except u.RunFileError as e:
        raise u.HMError("Could not launch the game: %s", e, e=e.e)


def read_settings() -> RawSettings:
    log.info("Read game settings: %s", c.GAME_CONFIG_PATH)
    with open(c.GAME_CONFIG_PATH) as f:
        settings = f.readlines()
    data = {k.strip(): v.strip() for k, v in (line.split("=") for line in settings)}
    log.debug("Parsed game settings: %s", data)
    return data


def write_settings(data: c.GameSettings) -> None:
    log.info("Write game settings: %s", c.GAME_CONFIG_PATH)
    text = "\n".join(f"{k} = {v}" for k, v in data.items())
    with open(c.GAME_CONFIG_PATH, "w") as f:
        f.write(text + "\n")


def check_settings(
    data: t.Optional[c.GameSettings] = None, raise_on_error: bool = False
) -> bool:
    if data is None:
        data = read_settings()
    diff = {k: (data[k], v) for k, v in c.GAME_SETTINGS.items() if not str(v) == data[k]}
    if not diff:
        return True
    if raise_on_error:
        raise u.HMError("Incorrect game settings")
    log.warning(
        "Incorrect game settings: \n\t%s",
        "\n\t".join((f"{k}: {v1}, expected {v2}" for k, (v1, v2) in diff.items())),
    )
    return False


def change_settings(data: t.Optional[c.GameSettings] = None) -> bool:
    if data is None:
        data = read_settings()
    original = data.copy()
    data.update({k: str(v) for k, v in c.GAME_SETTINGS.items()})
    if data == original:
        return False
    log.debug("Updated game settings: %s", data)
    write_settings(data)
    return True
