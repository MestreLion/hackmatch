# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Main module
"""

import logging
import sys
import time
import typing as t

from . import util as u
from . import gui

STEAM_URI = 'steam://rungameid/716490'

log = logging.getLogger(__name__)


def bot(argv: t.Optional[t.List[str]] = None):
    logging.basicConfig(level=logging.INFO, format='%(levelname)-7.7s: %(message)s')

    try:
        window = gui.activate_window('EXAPUNKS')
        bbox = gui.get_window_bbox(window)
        log.info("Window: %s", window)
    except u.HMError as e:
        log.warning(e)
        bbox = None
        log.info("Desktop: %s", gui.get_screen_size())

    img = gui.take_screenshot(bbox)
    img.show()

    benchmark(gui.take_screenshot, bbox)


def benchmark(func, *args, count=100, **kwargs):
    t0 = time.time()
    for _ in range(count):
        func(*args, **kwargs)
    t1 = time.time() - t0
    fps = count / t1
    avg = 1000 * t1 / count
    print(f'{fps:6.2f} FPS, {avg:5.1f}ms avg: {func.__name__}')


def main(argv: t.Optional[t.List[str]] = None):
    """Main CLI entry point"""
    try:
        sys.exit(bot(argv))
    except u.HMError as err:
        log.error(err)
        sys.exit(1)
    except Exception as err:
        log.critical(err, exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("Stopping...")
        sys.exit(2)  # signal.SIGINT.value
