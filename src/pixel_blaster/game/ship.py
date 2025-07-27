"""
ship.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

import typing

import numpy as np

from pixel_blaster.constants import (
    INITIAL_LIVES,
    MAX_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from pixel_blaster.game.util import wrap_position


class Ship:
    """Class representing the player's ship in the game."""

    _THRUST_POWER = 0.05  # Power of the ship's thrust
    _EXPLOSION_DURATION = 60  # Duration of the explosion in frames

    _EXPLOSION_COLORS: typing.ClassVar = [
        (255, 0, 0),
        (255, 165, 0),
        (255, 255, 0),
        (128, 0, 0),
        (201, 112, 112),
    ]

    def __init__(self) -> None:
        self._width = SCREEN_WIDTH
        self._height = SCREEN_HEIGHT

        self._lives = INITIAL_LIVES

        # ship position, initially centered on screen
        self._x = self._width // 2
        self._y = self._height // 2

        # ship angle (in degrees)
        self._direction = 0

        # ship velocity
        self._vx = 0
        self._vy = 0

        # thrusting state, when True, the ship accelerates
        self._thrusting = False

        # track exploding state
        self._exploding = 0

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

        self._gun_position = (0, 2)

    @property
    def x(self) -> int:
        """Get the x position of the ship."""
        return self._x

    @property
    def y(self) -> int:
        """Get the y position of the ship."""
        return self._y

    @property
    def position(self) -> tuple[float, float]:
        """Get the current position of the ship."""
        return self._x, self._y

    @property
    def gun_position(self) -> tuple[int, int]:
        """Get the position of the ship's gun."""
        return self._gun_position

    @property
    def color(self) -> tuple[int, int, int]:
        """Get the color of the ship."""
        if self.is_exploding:
            # return a random explosion color
            idx = np.random.randint(len(self._EXPLOSION_COLORS))
            return self._EXPLOSION_COLORS[idx]

        # normal ship color
        return self._color

    @property
    def direction(self) -> int:
        """Get the current bearing of the ship."""
        return self._direction

    @property
    def thrusting(self) -> bool:
        """Check if the ship is currently thrusting."""
        return self._thrusting

    @thrusting.setter
    def thrusting(self, value: bool) -> None:
        """Set whether the ship is currently thrusting."""
        self._thrusting = value

    @property
    def is_exploding(self) -> bool:
        """Check if the ship is currently exploding."""
        return self._exploding > 0

    @property
    def pixel_map(self) -> np.ndarray:
        """Get the pixel map of the ship, or a random pattern if exploding."""
        if self._exploding > 0:
            # Return a random pattern with the same shape as the ship
            # TODO: make a sequence of explosion frames instead of random

            explosion = np.random.choice([0, 1], size=self._pixel_map.shape, p=[0.7, 0.3]).astype(
                np.uint8
            )

            # set the corners to 0 to avoid sharp edges
            explosion[0, 0] = 0
            explosion[0, -1] = 0
            explosion[-1, 0] = 0
            explosion[-1, -1] = 0
            return explosion
        return self._pixel_map

    @property
    def lives(self) -> int:
        """Get the current number of lives of the ship."""
        return self._lives

    def update(self) -> None:
        """Update the ship's position and velocity based on current state."""
        # don't update position if the ship is exploding
        if self.is_exploding:
            return

        if self.thrusting:
            theta = np.radians(self.direction)
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

        # handle screen wrapping
        self._x, self._y = wrap_position((self._x, self._y))

    def update_explosion(self) -> None:
        """Update the explosion state of the ship."""
        if self._exploding > 0:
            self._exploding -= 1
        else:
            self._exploding = 0

    def reset(self) -> None:
        """Reset the ship to its initial state."""
        self._x = self._width // 2
        self._y = self._height // 2
        self._vx = self._vy = 0
        self._direction = 0
        self._exploding = 0
        self._thrusting = False

    def rotate_right(self) -> None:
        """Rotate the ship to the right."""
        self._direction += 5
        self._direction %= 360

    def rotate_left(self) -> None:
        """Rotate the ship to the left."""
        self._direction -= 5
        self._direction %= 360

    def handle_collision(self) -> None:
        """Handle collision with an asteroid."""
        if self._exploding > 0:
            # already exploding, ignore further collisions
            return

        self._lives -= 1
        if self._lives < 0:
            self._lives = 0

        # start the explosion sequence and stop ship's movement
        self._exploding = self._EXPLOSION_DURATION
        self._vx = self._vy = 0
