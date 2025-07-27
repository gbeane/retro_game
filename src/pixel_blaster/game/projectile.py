"""
projectile.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

import math
from typing import TYPE_CHECKING

from pixel_blaster.constants import (
    PROJECTILE_LIFETIME,
    PROJECTILE_SPEED,
)

from .util import wrap_position

if TYPE_CHECKING:
    from .ship import Ship


class Projectile:
    """Class representing a projectile fired by the ship.

    Args:
        source (Ship): The ship that fired the projectile.
    """

    def __init__(self, source: "Ship") -> None:
        self._speed = PROJECTILE_SPEED
        self._direction = source.direction
        self._frames_remaining = PROJECTILE_LIFETIME

        # Offset from ship center to gun position
        gun_dx = source.gun_position[0]
        gun_dy = source.gun_position[1]

        angle_rad = math.radians(self._direction)
        # Rotate offset by ship's direction
        rotated_dx = gun_dx * math.cos(angle_rad) - gun_dy * math.sin(angle_rad)
        rotated_dy = gun_dx * math.sin(angle_rad) + gun_dy * math.cos(angle_rad)

        # Set projectile position
        self._x = source.x + rotated_dx
        self._y = source.y + rotated_dy

    @property
    def is_alive(self) -> bool:
        """Check if the projectile is still alive."""
        return self._frames_remaining > 0

    @property
    def position(self) -> tuple[float, float]:
        """Get the current position of the projectile."""
        return self._x, self._y

    def update(self) -> None:
        """Update the projectile's position."""
        if not self.is_alive:
            # don't bother updating if the projectile is no longer alive
            return

        # Decrease the lifetime of the projectile
        self._frames_remaining -= 1

        # Convert angle to radians
        angle_rad = math.radians(self._direction)

        # Update the position based on speed and angle
        self._x += self._speed * math.sin(angle_rad)
        self._y -= self._speed * math.cos(angle_rad)

        # Screen wrapping
        self._x, self._y = wrap_position((self._x, self._y))
