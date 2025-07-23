"""
game.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

import enum
from typing import TYPE_CHECKING

from pixel_blaster.constants import SCREEN_HEIGHT, SCREEN_WIDTH

from .frame_buffer import FrameBuffer
from .ship import Ship

if TYPE_CHECKING:
    import numpy as np


class Game:
    """
    The Game class manages the core logic and state for the Pixel Blaster game.

    Responsibilities:
    - Maintains the game state, including the player's ship, score, and frame buffer.
    - Processes player input for movement and actions.
    - Updates the game state each frame.
    """

    class Key(enum.IntEnum):
        """Enum for game key inputs."""

        ANY = enum.auto()
        LEFT = enum.auto()
        RIGHT = enum.auto()
        UP = enum.auto()

    def __init__(self) -> None:
        self._width = SCREEN_WIDTH
        self._height = SCREEN_HEIGHT
        self._frame_buffer = FrameBuffer()
        self._score = 123456
        self._ship = Ship()
        self._show_splash_screen = True

    @property
    def frame_buffer(self) -> "np.ndarray":
        """Returns the current frame buffer."""
        return self._frame_buffer.frame_buffer

    @property
    def width(self) -> int:
        """Returns the width of the game screen."""
        return self._width

    @property
    def height(self) -> int:
        """Returns the height of the game screen."""
        return self._height

    def update(self) -> None:
        """Update the game state for the current frame."""
        self._frame_buffer.clear()

        if self._show_splash_screen:
            self._frame_buffer.draw_splash_screen()
        else:
            self._ship.update()
            self._frame_buffer.draw_ship(self._ship)
            self._frame_buffer.draw_lives(self._ship.lives)
            self._frame_buffer.draw_score(self._score)

    def handle_key(self, key: "Game.Key", pressed: bool) -> None:
        """Control player movement/fire."""
        # if the splash screen is shown, any key press will hide it
        if self._show_splash_screen and pressed:
            self._show_splash_screen = False
            return

        # otherwise handle game controls
        if key == self.Key.LEFT and pressed:
            self._ship.rotate_left()
        elif key == self.Key.RIGHT and pressed:
            self._ship.rotate_right()
        elif key == self.Key.UP:
            if pressed:
                self._ship.thrusting = True
            else:
                self._ship.thrusting = False
