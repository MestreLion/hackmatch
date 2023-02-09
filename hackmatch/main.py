# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
"""
Exapunks HACK*MATCH Bot
"""

__version__ = "0.1"

import argparse
import logging
import sys
import typing as t

from . import config as c
from . import game
from . import gui
from . import util as u

log = logging.getLogger(__name__)


def parse_args(argv: t.Optional[t.List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=c.COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-q",
        "--quiet",
        dest="loglevel",
        const=logging.WARNING,
        default=logging.INFO,
        action="store_const",
        help="Suppress informative messages.",
    )
    group.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        const=logging.DEBUG,
        action="store_const",
        help="Verbose mode, output extra info.",
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Benchmark mode, run for 30 seconds."
        " Best used with --quiet and game already launched.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch mode, read and solve board but do not play.",
    )

    parser.add_argument(
        "path",
        nargs="?",
        metavar="IMAGE",
        help="Ignore game window and solve %(metavar)s instead."
        " Useful when debugging with --verbose.",
    )

    args = parser.parse_args(argv)
    args.debug = args.loglevel == logging.DEBUG
    return args


def main(argv: t.Optional[t.List[str]] = None) -> None:
    args = parse_args(argv)
    u.setup_logging(args.loglevel)
    log.debug(args)
    c.init(args)

    if c.args.path:
        board = gui.get_board_from_path(path=c.args.path, debug=c.args.debug)
        if board is None:
            return
        log.info("\n%s", board)
        moves = board.solve()
        log.info("\t" + ", ".join(f"{_}" for _ in moves))
        return

    settings: c.GameSettings = game.read_settings()
    if not game.check_settings(settings):
        window = get_game_window(launch=False, activate=False)
        if window is not None:
            window.close()
            u.Timer(1).wait()  # so arbitrary!
        game.change_settings()

    window = get_game_window(activate=(c.args.path is None))
    assert window is not None
    log.info("Game window: %s", window)

    timer = u.Timer(60) if c.args.benchmark else u.FakeTimer(0)
    while not timer.expired:
        board = window.new_board(debug=c.args.debug)
        log.info(board)
        moves = board.solve()
        log.info(", ".join(f"{_}" for _ in moves))
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


def run(argv: t.Optional[t.List[str]] = None) -> None:
    """Main CLI entry point"""
    try:
        main(argv)
    except u.HMError as err:
        log.critical(err)
        sys.exit(1)
    except Exception as err:
        log.exception(err)
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("Stopped")
        sys.exit(2)
