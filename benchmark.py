# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
# ------------------------------------------------------------------------------
"""
Exapunks Hack*Match Bot testing
"""
import logging
import os
import sys
import time

# noinspection PyPackageRequirements
import mss
import PIL.Image
import PIL.ImageGrab
# noinspection PyPackageRequirements
import pyautogui


log = logging.getLogger(os.path.basename(os.path.splitext(__file__)[0]))
# ------------------------------------------------------------------------------


def fps_limit(fps=60):
    from hackmatch.util import FrameRateLimiter
    i = 0
    t0 = time.perf_counter()
    timer = FrameRateLimiter(fps)
    try:
        while True:
            i += 1
            timer.sleep()
    except KeyboardInterrupt:
        pass
    t1 = time.perf_counter()
    d = t1 - t0
    print(f"{i:6d} frames, {d:.2f}s, {i / d:5.1f} FPS")


def getpixel(x=0, y=0):
    rgb = PIL.ImageGrab.grab(xdisplay="").getpixel((x, y))
    print(rgb)


def bench_ss():
    def ss_mss():
        sct = mss.mss()
        ss = sct.grab(sct.monitors[1])
        return PIL.Image.frombytes("RGB", ss.size, ss.bgra, "raw", "BGRX")

    def ss_pyautogui():
        return pyautogui.grab()

    def ss_pil_hack():
        return PIL.ImageGrab.grab(xdisplay="")

    def ss_pil():
        return PIL.ImageGrab.grab()

    funcs = tuple(v for k, v in locals().items() if callable(v) and k.startswith('ss_'))
    if not funcs:
        return

    # make sure all images are the same
    assert len(set(func().tobytes() for func in funcs)) == 1

    for func in funcs:
        benchmark(func)

    funcs[0]().show()
# ------------------------------------------------------------------------------


def benchmark(func, count=100):
    t0 = time.time()
    for _ in range(count):
        func()
    t = time.time() - t0
    fps = count / t
    avg = 1000 * t / count
    print(f'{fps:6.2f} FPS, {avg:5.1f}ms avg: {func.__name__}')


def main():
    loglevel = logging.INFO
    # Lame argparse
    if '-v' in sys.argv[1:]:
        loglevel = logging.DEBUG
        sys.argv.remove('-v')
    logging.basicConfig(level=loglevel, format='%(levelname)-5.5s: %(message)s')

    funcs = tuple(k for k, v in globals().items() if callable(v) and k not in
                  ('main', 'benchmark'))
    if len(sys.argv) < 2:
        print("Usage: {} FUNCTION [ARGS...]\nAvailable functions:\n\t{}".format(
            __file__, "\n\t".join(funcs)))
        return

    func = sys.argv[1]
    args = sys.argv[2:]
    if func not in funcs:
        log.error("Function %r does not exist! Try one of:\n\t%s",
                  func, "\n\t".join(funcs))
        return

    def try_int(value):
        try:
            return int(value)
        except ValueError:
            return value
    args = [try_int(_) for _ in args]

    res = globals()[func](*args)
    if res is not None:
        print(repr(res))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
