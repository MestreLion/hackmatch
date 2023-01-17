# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Game solver
"""

import logging

log = logging.getLogger(__name__)


class Board:
    @classmethod
    def from_image(cls, image):
        obj = cls(image)
        ...
        return obj

    def __init__(self, image):
        self.image = image

    def solve(self):
        self.image.show()
