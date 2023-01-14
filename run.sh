#!/bin/bash
#
# Exapunks Hack*Match bot convenience launcher
#
# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
# ------------------------------------------------------------------------------
here=$(dirname "$(readlink -f "$0")")
python=$here/venv/bin/python

cd "$here" &&
exec "$python" -m hackmatch "$@"
