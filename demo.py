# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Demonstration of the bot architecture at its highest level
Fully working bot in less than 10 code lines
No bells and whistles, but the same AI and image recognition
"""

import time
from hackmatch import main

window = main.get_game_window()
while True:
    board = window.new_board()
    moves = board.solve()
    window.send_moves(moves)
    time.sleep(0.2)
