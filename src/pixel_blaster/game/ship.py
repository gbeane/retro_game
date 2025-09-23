"""
ship.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

import importlib.resources
import time
import typing
from pathlib import Path

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

    _ROTATE_STEP = 1  # Base turn step (degrees per turn step)
    _TURN_MULTIPLIER_MAX = 6  # Max multiplier applied to _ROTATE_STEP
    _TURN_BOOST_WINDOW_SEC = 0.16  # Time window (seconds) for chaining taps (~10 frames @60 FPS)
    _TURNS_FIRED_PER_LEVEL = (
        6  # Number turning actions to complete before increasing one boost level
    )
    _THRUST_POWER = 0.05  # Power of the ship's thrust
    _EXPLOSION_DURATION = 60  # Duration of the explosion in frames
    _RIGHT = 1
    _LEFT = -1

    _EXPLOSION_COLORS: typing.ClassVar = [
        (255, 0, 0),
        (255, 165, 0),
        (255, 255, 0),
        (128, 0, 0),
        (201, 112, 112),
    ]
    _EXPLOSION_SCALE = 2.5  # Explosion pixel map is larger than the ship's map (multiplier)

    def __init__(self) -> None:
        self._width = SCREEN_WIDTH
        self._height = SCREEN_HEIGHT

        self._lives = INITIAL_LIVES

        # ship position, initially centered on screen
        self._x = self._width // 2
        self._y = self._height // 2

        # ship angle (in degrees)
        self._bearing = 0

        # ship velocity
        self._vx = 0
        self._vy = 0

        # thrusting state, when True, the ship accelerates
        self._thrusting = False

        # track exploding state
        self._exploding_counter = 0

        # turning acceleration state
        self._last_turn_time = -1e9  # last turn input time (perf_counter domain)
        self._turning_multiplier = 1  # current multiplier on for rotation step size
        self._turn_chain_count = 0  # number of consecutive quick taps within the window

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

        with importlib.resources.as_file(
            importlib.resources.files("pixel_blaster.resources.sounds") / "blaster1.wav"
        ) as path:
            self._blaster_sound = path

        with importlib.resources.as_file(
            importlib.resources.files("pixel_blaster.resources.sounds") / "ship_explosion.wav"
        ) as path:
            self._explosion_sound = path

        with importlib.resources.as_file(
            importlib.resources.files("pixel_blaster.resources.sounds") / "thruster.wav"
        ) as path:
            self._thruster_sound = path

    @property
    def blaster_sound_path(self) -> Path:
        """Get the path to the blaster sound effect."""
        return self._blaster_sound

    @property
    def explosion_sound_path(self) -> Path:
        """Get the path to the explosion sound effect."""
        return self._explosion_sound

    @property
    def thruster_sound_path(self) -> Path:
        """Get the path to the thruster sound effect."""
        return self._thruster_sound

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
        return self._bearing

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
        return self._exploding_counter > 0

    @property
    def pixel_map(self) -> np.ndarray:
        """Get the pixel map of the ship, or a random pattern if exploding.

        note: color is handled separately, for example if the ship is exploding, the pixel map
        the pixel colors will be set to random explosion colors.
        """
        if self._exploding_counter > 0:
            # Explosion effect: circular area that grows over time with random fill.
            # Build an explosion array larger than the ship pixel map and fill a circle
            # that radiates from the center. Pixels inside the circle are turned on
            # randomly with higher density near the center and sparser near the edge.
            base_h, base_w = self._pixel_map.shape
            base = max(base_h, base_w)
            size = int(np.ceil(base * self._EXPLOSION_SCALE))
            # Ensure odd size so the center is well-defined
            if size % 2 == 0:
                size += 1

            # Coordinate grid centered at (cx, cy)
            cy = cx = size // 2

            # build a 2d array where each element is the distance from the center of the explosion grid
            yy, xx = np.indices((size, size))
            dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)

            # Radius grows with time (radiating outward)
            max_r = size // 2
            progress = 1.0 - (self._exploding_counter / self._EXPLOSION_DURATION)
            radius = max(1, int(progress * max_r))

            # mask out points outside the explosion radius
            mask = dist <= radius

            # Probability of pixel being "on" tapers from center (dense) to edge (sparse)
            with np.errstate(divide="ignore", invalid="ignore"):
                rnorm = np.clip(dist / max(radius, 1), 0, 1)
            prob = 0.8 * (1 - rnorm) + 0.2  # 1.0 at center -> 0.2 at edge

            # random fill based on probability mask, only within the explosion radius
            rnd = np.random.random((size, size))
            explosion = (mask & (rnd < prob)).astype(np.uint8)
            return explosion
        return self._pixel_map

    @property
    def lives(self) -> int:
        """Get the current number of lives of the ship."""
        return self._lives

    def award_new_life(self) -> None:
        """Award a new life to the ship."""
        self._lives += 1

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
        if self._exploding_counter > 0:
            self._exploding_counter -= 1
        else:
            self._exploding_counter = 0

    def reset(self) -> None:
        """Reset the ship to its initial state."""
        self._x = self._width // 2
        self._y = self._height // 2
        self._vx = self._vy = 0
        self._bearing = 0
        self._exploding_counter = 0
        self._thrusting = False

    def _apply_turn(self, direction: int) -> None:
        """Apply a left/right rotation with acceleration when turn signals are repeated quickly.

        direction = +1 for right, -1 for left.

        Todo: consider changing direction to an enum
        """
        now = time.perf_counter()

        # If this turn happens within the boost window, extend the input chain; else reset.
        if (now - self._last_turn_time) <= self._TURN_BOOST_WINDOW_SEC:
            self._turn_chain_count += 1
        else:
            self._turn_chain_count = 0
            self._turning_multiplier = 1
        self._last_turn_time = now

        # Each N turn inputs increases multiplier up to the cap
        level = 1 + (self._turn_chain_count // self._TURNS_FIRED_PER_LEVEL)
        self._turning_multiplier = min(level, self._TURN_MULTIPLIER_MAX)

        step = self._ROTATE_STEP * self._turning_multiplier
        self._bearing = (self._bearing + direction * step) % 360

    def rotate_right(self) -> None:
        """Rotate the ship to the right."""
        self._apply_turn(self._RIGHT)

    def rotate_left(self) -> None:
        """Rotate the ship to the left."""
        self._apply_turn(self._LEFT)

    def handle_collision(self) -> None:
        """Handle collision with an asteroid."""
        if self._exploding_counter > 0:
            # already exploding, ignore further collisions
            return

        self._lives -= 1
        if self._lives < 0:
            self._lives = 0

        # start the explosion sequence and stop ship's movement
        self._exploding_counter = self._EXPLOSION_DURATION
        self._vx = self._vy = 0

        # if the ship was thrusting, stop it and stop the thruster sound
        if self._thrusting:
            self._thrusting = False
