"""
util.py

common utility functions for the Pixel Blaster game

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

from pixel_blaster.constants import SCREEN_HEIGHT, SCREEN_WIDTH, TOP_MARGIN


def wrap_position(position: tuple[float, float]) -> tuple[float, float]:
    """Wrap the position around the screen boundaries."""
    x, y = position
    # Screen wrapping - width
    x %= SCREEN_WIDTH

    # take the score area at top of screen into account so that is not considered part of the play area
    if y < TOP_MARGIN:
        y = SCREEN_HEIGHT - 1
    elif y > SCREEN_HEIGHT:
        y = TOP_MARGIN + 1

    return x, y
