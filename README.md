# Cross-platform Exapunks HACK*MATCH bot in Python

Yet another bot for [Exapunks][1]' amazing (and annoyingly hard)
**HACK*MATCH** arcade minigame.

Want to score 100,000 points and grab the [hardest of its achievements][2]
and join the 0,7% club? Look no further!

Don't feel frustrated if you, like me, have no skills for a NES-like reflex game
and think such arcade game have no place in a logic/puzzle _programming_ game
such as Exapunks.

Why create another bot? Well, I felt it would not be cheating if I
_programmed_ the bot myself! **Exapunks** is all about coding and hacking,
so creating a bot to hack _it_ fits in perfectly!

---
Features
--------
- Cross Platform, works on Windows, macOS and Linux
- Works on several resolutions, from 1920x1200 to 1366x768
- Read and write game settings to get user's current keyboard mapping and to
  automatically turn off CRT effects.
- Launch the game if needed, using Steam's [`steam://rungameid/716490`]() game URI.
- Pure Python: easy to understand, install and run, no compiler or other tools needed.
- Command-line arguments to benchmark, debug, watch-only and more.

### Heavily inspired by and adapted from:

- [Fidel-solver's exapunks-hack-match bot](https://github.com/fidel-solver/exapunks-hack-match)
    - C++, X11 and 1600x900 only, requires custom keys, has fuzzy tolerance on colors.
    - Arguably the most well-known reference, possibly the first bot published.
    - +500K points recorded on YouTube.

- [Laelath's hack-match-bot](https://github.com/laelath/hack-match-bot)
    - Rust, X11 and 1920x1080 only, requires default keys and no CRT, no fuzziness.
    - An elegant code with great insights on image parsing and board solving.
    - +8M points recorded on YouTube.

And special thanks to [Dissecting fidelSolver's Game Bot for Playing Hack*Match][3],
an amazing presentation by Alan Shen that helped me understand the basic concepts
and building blocks of both above projects.

---
Installing
----------

Run this to install the bot and its dependencies, preferably in a virtual environment:

    pip3 install hackmatch

This bot is written in Python and uses PyAutoGUI, which has some pre-requisites
beyond its `pip` install. For Debian, Ubuntu and derivatives, just run:

    sudo apt install python3-tk

For instructions on all platforms, see the [PyAutoGUI documentation][4].

I've also included a tool to automatically create the python virtual environment,
`apt`-install the requirements and `pip`-install dependencies and the bot itself,
all in a single step:

    ./install.sh

> _**Note**_: even if code itself is compatible with earlier Python versions,
> some dependencies require **Python 3.7**. It was fully tested on Python 3.8.

Usage
-----

For basic usage, just run:

    hackmatch-bot

- If the game is installed in Steam, it will automatically launch Exapunks
if not already running.
- Keep the bot running (i.e., leave the terminal open), and manually enter and
start the HACK*MATCH minigame.
- Profit!

Debugging, testing or fine-tuning?

```console
$ hackmatch-bot --help
usage: hackmatch-bot [-h] [-q | -v] [--benchmark] [--watch] [--solve-time TIME]
                                    [--board TEXT | IMAGE]

positional arguments:
  IMAGE              Ignore game window and solve IMAGE instead.
                     Useful when debugging with --verbose.

optional arguments:
  -h, --help         show this help message and exit
  -q, --quiet        Suppress informative messages.
  -v, --verbose      Verbose mode, output extra info.
  --benchmark        Benchmark mode, run for 30 seconds.
                       Best used with --quiet and game already launched.
  --watch            Watch mode, read and solve board but do not play.
  --solve-time TIME  Time in milliseconds to solve each parsed board,
                       0 for unlimited. [Default: 850 ms]
  --board TEXT       Ignore game window and solve TEXT instead.

Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
```

---
Contributing
------------

Patches are welcome! Fork, hack, request pull!

See the [To-Do List](./TODO.md) for more updated technical information and
planned features.

If you find a bug or have any enhancement request, please to open a
[new issue](../../issues/new)


Author
------

Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>

License and Copyright
---------------------
```
Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
```

[1]: https://store.steampowered.com/app/716490/EXAPUNKS/
[2]: https://steamcommunity.com/stats/716490/achievements
[3]: https://sunzenshen.github.io/presentations/2018/12/08/dissecting-hackmatch-solver.html
[4]: https://pyautogui.readthedocs.io/en/latest/install.html
