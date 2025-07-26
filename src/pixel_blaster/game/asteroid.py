"""
asteroid.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

import enum

import numpy as np

from pixel_blaster.constants import SCREEN_HEIGHT, SCREEN_WIDTH, TOP_MARGIN


class Asteroid:
    """Class representing an asteroid in the game."""

    class Size(enum.IntEnum):
        """Enum for asteroid sizes."""

        SMALL = enum.auto()
        MEDIUM = enum.auto()
        LARGE = enum.auto()

    pixmap_small = np.asarray(
        [
            [0, 1, 1, 0, 0],
            [1, 1, 1, 1, 0],
            [1, 1, 1, 1, 1],
            [0, 1, 1, 1, 0],
            [0, 0, 1, 0, 0],
        ],
        dtype=np.uint8,
    )

    pixmap_medium = np.asarray(
        [
            [0, 0, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 1, 1, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    pixmap_large = np.asarray(
        [
            [0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    def __init__(
        self, x: int, y: int, size: "Asteroid.Size", color: tuple[int, int, int] = (128, 128, 128)
    ) -> None:
        self._x = x
        self._y = y
        self._size = size
        self._color = color

        # generate random direction and speed
        if size == Asteroid.Size.LARGE:
            speed = np.random.uniform(0.1, 0.4)
        elif size == Asteroid.Size.MEDIUM:
            speed = np.random.uniform(0.3, 0.5)
        else:  # SMALL
            speed = np.random.uniform(0.5, 0.8)
        angle = np.random.uniform(0, 2 * np.pi)

        # set the velocity components based on the angle and speed
        self._vx = np.cos(angle) * speed
        self._vy = np.sin(angle) * speed

    @property
    def x(self) -> int:
        """Get the x position of the asteroid."""
        return self._x

    @property
    def y(self) -> int:
        """Get the y position of the asteroid."""
        return self._y

    @property
    def size(self) -> "Asteroid.Size":
        """Get the size of the asteroid."""
        return self._size

    @property
    def color(self) -> tuple[int, int, int]:
        """Get the color of the asteroid."""
        return self._color

    @property
    def pixel_map(self) -> np.ndarray:
        """Get the pixel map of the asteroid based on its size."""
        if self._size == Asteroid.Size.SMALL:
            return self.pixmap_small
        elif self._size == Asteroid.Size.MEDIUM:
            return self.pixmap_medium
        elif self._size == Asteroid.Size.LARGE:
            return self.pixmap_large
        else:
            raise NotImplementedError(f"Asteroid size {self._size} not implemented.")

    def update(self) -> None:
        """Update the asteroid's position based on its velocity."""
        self._x += self._vx
        self._y += self._vy

        # Screen wrapping
        self._x %= SCREEN_WIDTH

        # take the score area at top of screen into account so that is not considered part of the play area
        if self._y < TOP_MARGIN:
            self._y = SCREEN_HEIGHT
        elif self._y > SCREEN_HEIGHT:
            self._y = TOP_MARGIN
