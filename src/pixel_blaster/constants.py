"""
constants.py

Pixel Blaster
Copyright (c) 2025 Glen Beane

This module defines constants used throughout the Pixel Blaster game.
"""

TOP_MARGIN = 15  # Space for score and lives between top of screen and play area in pixels
SCORE_TOP_MARGIN = 3  # Space between score and top of screen in pixels
LIVES_RIGHT_MARGIN = 10  # Space between right edge of screen and lives display in pixels
SCREEN_WIDTH = 192  # Width of the game screen in pixels
SCREEN_HEIGHT = 160  # Height of the game screen in pixels
MAX_SPEED = 5  # Maximum speed of the ship in pixels per frame
INITIAL_LIVES = 4
MAX_LIVES = 99
MAX_SCORE = 999999
SHIP_RESPAWN_DELAY = 120  # Frames to wait before respawning the ship after destruction
ASTEROID_SPAWN_COUNT = 12  # Initial number of asteroids to spawn at the start of the game
PROJECTILE_SPEED = 6  # Speed of the ship's projectiles in pixels per frame
PROJECTILE_LIFETIME = 12  # Lifetime of a projectile in frames
SCORE_HIT_LARGE = 20
SCORE_HIT_MEDIUM = 50
SCORE_HIT_SMALL = 100
ASTEROID_SPAWN_RADIUS = 40  # Radius around the ship where asteroids can spawn
MAX_ASTEROIDS = 20  # Maximum number of asteroids allowed on screen at once
POINTS_FOR_NEW_LIFE = 5000  # Points required to gain an extra life
