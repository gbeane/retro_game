"""
game.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

import enum

import numpy as np

from pixel_blaster.constants import SCREEN_HEIGHT, SCREEN_WIDTH, SHIP_RESPAWN_DELAY, TOP_MARGIN

from .asteroid import Asteroid
from .frame_buffer import FrameBuffer
from .ship import Ship


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
        self._respawn_countdown = 0

        # add a few asteroids for testing purposes
        self._asteroids = []
        self._spawn_asteroids(12)

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

    @property
    def _respawn_delay_active(self) -> bool:
        """Check if the respawn delay is active."""
        return self._respawn_countdown > 0

    def update(self) -> None:
        """Update the game state for the current frame."""
        self._frame_buffer.clear()

        if self._show_splash_screen:
            self._frame_buffer.draw_splash_screen()
            return

        for asteroid in self._asteroids:
            asteroid.update()
            self._frame_buffer.draw_asteroid(asteroid)

        if self._ship.is_exploding:
            self._frame_buffer.draw_ship(self._ship)
            self._ship.update_explosion()

            # has the explosion finished?
            if not self._ship.is_exploding and self._ship.lives > 0:
                self._start_respawn_delay()
                self._ship.reset()
        elif self._respawn_delay_active:
            self._update_respawn_delay()

        elif self._ship.lives <= 0:
            # if the ship has no lives left, show the game over screen
            self._frame_buffer.draw_game_over()
        else:
            self._ship.update()
            if self._check_ship_collision():
                self._ship.handle_collision()
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

    def _spawn_asteroids(self, count: int) -> None:
        """Add a specified number of asteroids to the game.

        Asteroids will be spawned at random locations on the edges of the play area
        and will initialize their own velocity and direction.
        """
        edge_margin = 40
        for _ in range(count):
            edge = np.random.choice(["top", "bottom", "left", "right"])
            if edge == "top":
                x = np.random.randint(0, SCREEN_WIDTH)
                y = np.random.randint(TOP_MARGIN, edge_margin + TOP_MARGIN)
            elif edge == "bottom":
                x = np.random.randint(0, SCREEN_WIDTH)
                y = np.random.randint(SCREEN_HEIGHT - edge_margin, SCREEN_HEIGHT)
            elif edge == "left":
                x = np.random.randint(0, edge_margin)
                y = np.random.randint(TOP_MARGIN, SCREEN_HEIGHT)
            else:  # right
                x = np.random.randint(SCREEN_WIDTH - edge_margin, SCREEN_WIDTH)
                y = np.random.randint(TOP_MARGIN, SCREEN_HEIGHT)

            size = np.random.choice(
                [Asteroid.Size.LARGE, Asteroid.Size.MEDIUM, Asteroid.Size.SMALL], p=[0.6, 0.3, 0.1]
            )

            # for now pick a random color for the asteroid
            # maybe we want to choose from a fixed color palette in the future
            color = tuple(np.random.randint(64, 192, size=3))
            self._asteroids.append(Asteroid(x=x, y=y, size=size, color=color))

    def _check_ship_collision(self) -> bool:
        """Check if the ship collides with any asteroid and handle the collision."""
        ship_box = self._get_bounding_box(self._ship.x, self._ship.y, self._ship.pixel_map)
        for asteroid in self._asteroids:
            asteroid_box = self._get_bounding_box(asteroid.x, asteroid.y, asteroid.pixel_map)
            if self._bounding_box_overlap(ship_box, asteroid_box):
                return True
        return False

    @staticmethod
    def _get_bounding_box(
        x: int, y: int, pixmap: np.ndarray, shrink: float = 0.8
    ) -> tuple[int, int, int, int]:
        """Calculate the bounding box for a pixel map.

        Args:
            x (int): The x-coordinate of the pixel map.
            y (int): The y-coordinate of the pixel map.
            pixmap (np.ndarray): The pixel map to calculate the bounding box for.
            shrink (float): Factor to shrink the bounding box by.

        Returns:
            tuple[int, int, int, int]: The bounding box as (x1, y1, x2, y2).
        """
        h, w = pixmap.shape
        cx, cy = x, y
        half_w = w * shrink / 2
        half_h = h * shrink / 2
        return (
            round(cx - half_w),
            round(cy - half_h),
            round(cx + half_w),
            round(cy + half_h),
        )

    @staticmethod
    def _bounding_box_overlap(
        box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]
    ) -> bool:
        """Check if two bounding boxes overlap.

        Args:
            box1 (tuple[int, int, int, int]): The first bounding box as (x1, y1, x2, y2).
            box2 (tuple[int, int, int, int]): The second bounding box as (x1, y1, x2, y2).

        Returns:
            bool: True if the boxes overlap, False otherwise.
        """
        return not (
            box1[2] < box2[0] or box1[0] > box2[2] or box1[3] < box2[1] or box1[1] > box2[3]
        )

    def _start_respawn_delay(self):
        self._respawn_countdown = SHIP_RESPAWN_DELAY

    def _update_respawn_delay(self):
        """Update the respawn delay countdown."""
        if self._respawn_countdown > 0:
            self._respawn_countdown -= 1
