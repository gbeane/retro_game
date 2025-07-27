"""
game.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

import enum
from collections.abc import MutableSequence, Sequence
from typing import TypeVar

import numpy as np

from pixel_blaster.constants import (
    ASTEROID_SPAWN_COUNT,
    ASTEROID_SPAWN_RADIUS,
    MAX_ASTEROIDS,
    MAX_LIVES,
    MAX_SCORE,
    POINTS_FOR_NEW_LIFE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIP_RESPAWN_DELAY,
    TOP_MARGIN,
)

from .asteroid import Asteroid
from .frame_buffer import FrameBuffer
from .projectile import Projectile
from .ship import Ship

T = TypeVar("T")


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
        FIRE = enum.auto()

    def __init__(self) -> None:
        self._width = SCREEN_WIDTH
        self._height = SCREEN_HEIGHT
        self._frame_buffer = FrameBuffer()
        self._score = 0
        self._ship = Ship()
        self._show_splash_screen = True
        self._respawn_countdown = 0
        self._level = 1
        self._next_bonus_life = POINTS_FOR_NEW_LIFE

        self._asteroids = []
        self._spawn_asteroids(ASTEROID_SPAWN_COUNT)

        # add a projectile for testing purposes
        self._projectiles = []

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
        """Update the game state for the current frame.

        Handles most of the game logic, including updating the ship, projectiles, and asteroids.
        Clears the frame buffer and draws the current game state, including the ship, asteroids,
        projectiles, score, and lives. If the ship has no lives left, it draws the game over screen.
        """
        self._frame_buffer.clear()

        if self._show_splash_screen:
            self._frame_buffer.draw_splash_screen()
            return

        self._update_projectiles()
        self._update_asteroids()
        self._update_ship()
        self._frame_buffer.draw_lives(self._ship.lives)
        self._frame_buffer.draw_score(self._score)

        if self._ship.lives == 0:
            self._frame_buffer.draw_game_over()
        elif len(self._asteroids) == 0:
            self._level += 1
            self._spawn_asteroids(ASTEROID_SPAWN_COUNT)

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
        elif (
            key == self.Key.FIRE
            and pressed
            and not self._respawn_delay_active
            and not self._ship.is_exploding
        ):
            # fire a projectile only if the ship is not exploding or in respawn delay
            self._projectiles.append(Projectile(self._ship))

    def _update_projectiles(self) -> None:
        """Update all projectiles and check for collisions with asteroids.

        If a projectile collides with an asteroid, both the projectile and the asteroid
        are removed from their respective lists, and the score is updated based on the
        asteroid's size.
        """
        # track projectiles and asteroids to remove
        projectiles_to_remove = []
        asteroids_to_remove = []
        new_asteroids = []

        # update each projectile and check for collisions with asteroids
        for projectile in self._projectiles:
            projectile.update()

            if projectile.is_alive:
                # after updating, projectile is still alive so we need to draw it and check for collisions
                self._frame_buffer.draw_projectile(projectile)
                if hit_asteroid := self._check_projectile_collision(projectile):
                    projectiles_to_remove.append(projectile)
                    asteroids_to_remove.append(hit_asteroid)
                    self._update_score(hit_asteroid.points)
                    # handle asteroid hit, which may result in new asteroids being spawned
                    new_asteroids.extend(self._handle_asteroid_hit(hit_asteroid))
            else:
                # projectile has reached its end of life, mark it for removal
                projectiles_to_remove.append(projectile)

        self._remove_items(self._projectiles, projectiles_to_remove)
        self._remove_items(self._asteroids, asteroids_to_remove)

        if new_asteroids:
            # if there are new asteroids spawned, add them to the game
            self._asteroids.extend(new_asteroids)

    def _update_asteroids(self) -> None:
        """Update all asteroids and draw them on the frame buffer."""
        for asteroid in self._asteroids:
            asteroid.update()
            self._frame_buffer.draw_asteroid(asteroid)

    def _update_ship(self) -> None:
        """Update the ship's state and handle possible collisions between the ship and asteroids."""
        if self._ship.is_exploding:
            # ship is exploding, draw the explosion animation
            self._frame_buffer.draw_ship(self._ship)
            self._ship.update_explosion()

            # if the explosion is done, reset the ship
            if not self._ship.is_exploding and self._ship.lives > 0:
                self._start_respawn_delay()
                self._ship.reset()
        elif self._respawn_delay_active:
            # the ship doesn't need to be drawn if we're waiting for respawn
            self._update_respawn_delay()
        elif self._ship.lives:
            # ship is alive.
            self._ship.update()
            if self._check_ship_collision():
                self._ship.handle_collision()
            self._frame_buffer.draw_ship(self._ship)

    @staticmethod
    def _remove_items(collection: MutableSequence[T], items: Sequence[T]) -> None:
        """Remove specified items from a collection."""
        for item in items:
            if item in collection:
                collection.remove(item)

    def _check_projectile_collision(self, projectile: Projectile) -> Asteroid | None:
        """Check if a projectile collides with any asteroid.

        Args:
            projectile (Projectile): The projectile to check for collisions.

        Returns:
            Asteroid | None: The asteroid that was hit by the projectile, or None if no collision occurred.
        """
        for asteroid in self._asteroids:
            asteroid_box = self._get_bounding_box(asteroid.x, asteroid.y, asteroid.pixel_map, 0.9)
            if self._pixel_in_bounding_box(
                round(projectile.position[0]), round(projectile.position[1]), asteroid_box
            ):
                return asteroid
        return None

    def _spawn_asteroids(self, count: int) -> None:
        """Add a specified number of asteroids to the game.

        Asteroids will be spawned at random locations on the edges of the play area
        and will initialize their own velocity and direction.
        """
        edge_margin = ASTEROID_SPAWN_RADIUS
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
        """Check if the ship collides with any asteroid and handle the collision.

        Returns:
            bool: True if the ship has collided with an asteroid, False otherwise.
        """
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

    @staticmethod
    def _pixel_in_bounding_box(x: int, y: int, box: tuple[int, int, int, int]) -> bool:
        """Check if a pixel is within a bounding box.

        Args:
            x (int): The x-coordinate of the pixel.
            y (int): The y-coordinate of the pixel.
            box (tuple[int, int, int, int]): The bounding box as (x1, y1, x2, y2).

        Returns:
            bool: True if the pixel is within the bounding box, False otherwise.
        """
        return box[0] <= x < box[2] and box[1] <= y < box[3]

    def _start_respawn_delay(self) -> None:
        """Start the respawn delay countdown for the ship."""
        self._respawn_countdown = SHIP_RESPAWN_DELAY

    def _update_respawn_delay(self) -> None:
        """Update the respawn delay countdown."""
        if self._respawn_countdown > 0:
            self._respawn_countdown -= 1

    def _handle_asteroid_hit(self, asteroid: Asteroid) -> list[Asteroid]:
        """Handle the event when an asteroid is hit by a projectile or player ship.

        Returns:
            list[Asteroid]: A list of new asteroids if the asteroid was large or medium and needs to be split.

        Note: if we are at the maximum number of asteroids, we will not spawn new ones.
        Instead, a large will be replaced by a single medium and a medium by a single small asteroid.
        """
        # when new asteroids are spawned, their new heading is adjusted by a fixed angle
        angles = (
            [20, -20]
            if not len(self._asteroids) >= MAX_ASTEROIDS
            else [np.random.choice([20, -20])]
        )

        def permute_velocity(
            _velocity: tuple[float, float], angle_deg: float, size
        ) -> tuple[float, float]:
            """Permute the parent asteroid's velocity to create a new asteroid's velocity."""
            v = np.array(_velocity)
            angle_rad = np.deg2rad(angle_deg)
            rotation_matrix = np.array(
                [[np.cos(angle_rad), -np.sin(angle_rad)], [np.sin(angle_rad), np.cos(angle_rad)]]
            )
            rotated_v = rotation_matrix @ v
            norm = np.linalg.norm(rotated_v)
            if norm == 0:
                rotated_v = np.array([1.0, 0.0])
                norm = 1.0
            speed = Asteroid.initialize_asteroid_speed(size)
            new_v = rotated_v / norm * speed
            return float(new_v[0]), float(new_v[1])

        new_asteroids = []
        if asteroid.size == Asteroid.Size.LARGE:
            for angle in angles:
                velocity = permute_velocity(asteroid.velocity, angle, Asteroid.Size.MEDIUM)
                new_asteroids.append(
                    Asteroid(
                        x=asteroid.x,
                        y=asteroid.y,
                        size=Asteroid.Size.MEDIUM,
                        color=asteroid.color,
                        velocity=velocity,
                    )
                )
        elif asteroid.size == Asteroid.Size.MEDIUM:
            for angle in angles:
                velocity = permute_velocity(asteroid.velocity, angle, Asteroid.Size.SMALL)
                new_asteroids.append(
                    Asteroid(
                        x=asteroid.x,
                        y=asteroid.y,
                        size=Asteroid.Size.SMALL,
                        color=asteroid.color,
                        velocity=velocity,
                    )
                )
        return new_asteroids

    def _update_score(self, points: int) -> None:
        """Update the game score and handle bonus lives."""
        if self._score == MAX_SCORE:
            return

        # award points
        self._score += points
        if self._score >= self._next_bonus_life and self._ship.lives < MAX_LIVES:
            self._ship.award_new_life()
            self._next_bonus_life += POINTS_FOR_NEW_LIFE

        # cap score
        if self._score > MAX_SCORE:
            self._score = MAX_SCORE
