"""
ship.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

import numpy as np

from pixel_blaster.constants import (
    INITIAL_LIVES,
    MAX_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TOP_MARGIN,
)


class Ship:
    """Class representing the player's ship in the game."""

    _THRUST_POWER = 0.05  # Power of the ship's thrust

    def __init__(self) -> None:
        self._width = SCREEN_WIDTH
        self._height = SCREEN_HEIGHT

        self._lives = INITIAL_LIVES

        # ship position, initially centered on screen
        self._x = self._width // 2
        self._y = self._height // 2

        # ship angle (in degrees)
        self._angle = 0

        # ship velocity
        self._vx = 0
        self._vy = 0

        # thrusting state, when True, the ship accelerates
        self._thrusting = False

        # Pixel map representing the ship's shape
        self._pixel_map = np.asarray(
            [
                [0, 0, 1, 0, 0],
                [0, 0, 1, 0, 0],
                [0, 1, 1, 1, 0],
                [0, 1, 1, 1, 0],
                [1, 1, 1, 1, 1],
            ],
            dtype=np.uint8,
        )

        self._color = (208, 112, 112)

    @property
    def x(self) -> int:
        """Get the x position of the ship."""
        return self._x

    @property
    def y(self) -> int:
        """Get the y position of the ship."""
        return self._y

    @property
    def color(self) -> tuple[int, int, int]:
        """Get the color of the ship."""
        return self._color

    @property
    def angle(self) -> int:
        """Get the current angle of the ship."""
        return self._angle

    @property
    def thrusting(self) -> bool:
        """Check if the ship is currently thrusting."""
        return self._thrusting

    @thrusting.setter
    def thrusting(self, value: bool) -> None:
        """Set whether the ship is currently thrusting."""
        self._thrusting = value

    @property
    def pixel_map(self) -> np.ndarray:
        """Get the pixel map of the ship."""
        return self._pixel_map

    @property
    def lives(self) -> int:
        """Get the current number of lives of the ship."""
        return self._lives

    def update(self) -> None:
        """Update the ship's position and velocity based on current state."""
        if self.thrusting:
            theta = np.radians(self.angle)
            self._vx += self._THRUST_POWER * np.sin(theta)
            self._vy += -self._THRUST_POWER * np.cos(theta)

        # Limit speed to a maximum value
        speed = np.sqrt(self._vx**2 + self._vy**2)
        if speed > MAX_SPEED:
            scale = MAX_SPEED / speed
            self._vx *= scale
            self._vy *= scale

        # Apply friction
        self._vx *= 0.995
        self._vy *= 0.995

        # Update position
        self._x += self._vx
        self._y += self._vy

        # Screen wrapping
        self._x %= self._width

        # take the score area at top of screen into account so that is not considered part of the play area
        if self._y < TOP_MARGIN:
            self._y = self._height
        elif self._y > self._height:
            self._y = TOP_MARGIN

    def rotate_right(self) -> None:
        """Rotate the ship to the right."""
        self._angle += 5
        self._angle %= 360

    def rotate_left(self) -> None:
        """Rotate the ship to the left."""
        self._angle -= 5
        self._angle %= 360
