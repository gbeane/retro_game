"""
frame_buffer.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

import numpy as np

from pixel_blaster.constants import (
    LIVES_RIGHT_MARGIN,
    MAX_LIVES,
    MAX_SCORE,
    SCORE_TOP_MARGIN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TOP_MARGIN,
)

from .font import Font, ScoreFont
from .ship import Ship


class FrameBuffer:
    """A class representing the frame buffer for the game screen."""

    def __init__(self) -> None:
        self._width = SCREEN_WIDTH
        self._height = SCREEN_HEIGHT
        self._frame_buffer = np.zeros((self._height, self._width, 3), dtype=np.uint8)
        self._text_font = Font()
        self._score_font = ScoreFont()

    @property
    def frame_buffer(self) -> np.ndarray:
        """Returns the current frame buffer."""
        return self._frame_buffer

    @property
    def width(self) -> int:
        """Returns the width of the game screen."""
        return self._width

    @property
    def height(self) -> int:
        """Returns the height of the game screen."""
        return self._height

    def draw_text_right_aligned(
        self,
        x: int,
        y: int,
        text: str,
        font: Font,
        color: tuple = (255, 255, 255),
    ) -> None:
        """Draw right-aligned text on the frame buffer.

        Args:
            x (int): The x-coordinate where the text should be drawn.
            y (int): The y-coordinate where the text should be drawn.
            text (str): The text to draw.
            font (Font): The font object used for rendering text.
            color (tuple): RGB color tuple for the text, default is white.

        This is a common use case for drawing text (scores and lives).
        """
        # Reverse the string so we can draw from right to left
        text = text[::-1]

        x_offset = x
        y_offset = y

        for char in text:
            pixel_map = font.get_character(char)
            h, w = pixel_map.shape

            # move the x_offset left by the width of the character
            x_offset -= w

            # get the non-zero pixel coordinates in the font character bitmap
            ys, xs = np.nonzero(pixel_map)

            # Adjust the coordinates to the current x_offset and y_offset
            abs_xs = xs + x_offset
            abs_ys = ys + y_offset

            # create a mask so we can set the pixels in the frame buffer that correspond to the character
            mask = (abs_xs >= 0) & (abs_xs < self.width) & (abs_ys >= 0) & (abs_ys < self.height)
            self._frame_buffer[abs_ys[mask], abs_xs[mask]] = color

            x_offset -= 2  # Add some spacing between characters

    def draw_text_centered(
        self,
        x: int,
        y: int,
        text: str,
        font: Font,
        color: tuple = (255, 255, 255),
    ) -> None:
        """Draw centered text on the frame buffer.

        Args:
            x (int): The x-coordinate where the text should be centered.
            y (int): The y-coordinate where the text should be drawn.
            text (str): The text to draw.
            font (Font): The font object used for rendering text.
            color (tuple): RGB color tuple for the text, default is white.

        Since we already implemented a right-aligned text drawing function for scores and lives,
        we can use it to center the text by adjusting the x offset by half of the width of the text.
        """
        text_width = sum(font.get_character(char).shape[1] for char in text) + 2 * (len(text) - 1)
        x_offset = x + text_width // 2
        self.draw_text_right_aligned(x_offset, y, text, font, color)

    def draw_ship(self, ship: Ship) -> None:
        """Draw the ship on the frame buffer."""
        theta = np.radians(ship.angle)
        cos_theta, sin_theta = np.cos(theta), np.sin(theta)

        h, w = ship.pixel_map.shape
        cx, cy = w // 2, h // 2

        # Get indices of nonzero pixels
        ys, xs = np.nonzero(ship.pixel_map)
        for py, px in zip(ys, xs, strict=False):
            # Calculate relative position to center of the ship
            rel_x = px - cx
            rel_y = py - cy

            # Rotate the pixel position
            rx = rel_x * cos_theta - rel_y * sin_theta
            ry = rel_x * sin_theta + rel_y * cos_theta

            # Translate to absolute position
            fx = round(ship.x + rx)
            fy = round(ship.y + ry)

            # if pixel coordinates are within bounds set the pixel color in frame buffer
            # ensures that the ship is drawn only within the play area, which does not include the score area at the top
            if TOP_MARGIN <= fy < self.height and 0 <= fx < self.width:
                self._frame_buffer[fy, fx] = ship.color

    def draw_score(self, score: int, color=(255, 0, 0)) -> None:
        """Draw the score right-aligned at the center of the frame buffer.

        Args:
            score (int): The score to draw.
            color (tuple): RGB color tuple for the text, default is red.
        """
        # allow scores up to 6 digits
        if not (0 <= score <= MAX_SCORE):
            raise ValueError(f"Score should be in the range 0-{MAX_SCORE}.")

        score_str = str(score)
        x = self.width // 2
        y = SCORE_TOP_MARGIN
        self.draw_text_right_aligned(x, y, score_str, self._score_font, color)

    def draw_lives(self, lives: int, color=(255, 0, 0)) -> None:
        """Draw the number of lives (0-99) right-aligned on the frame buffer.

        Args:
            lives (int): The number of lives to draw.
            color (tuple): RGB color tuple for the text, default is red.
        """
        if not (0 <= lives <= MAX_LIVES):
            raise ValueError(f"Lives should be in the range 0-{MAX_LIVES}.")

        lives_str = str(lives)
        x = self.width - LIVES_RIGHT_MARGIN
        y = SCORE_TOP_MARGIN
        self.draw_text_right_aligned(x, y, lives_str, self._score_font, color)

    def draw_splash_screen(self) -> None:
        """Draw the splash screen on the frame buffer."""
        # Draw the title text
        self.draw_text_centered(
            x=self.width // 2,
            y=20,
            text="PIXEL BLASTER",
            font=self._text_font,
            color=(255, 165, 0),
        )

        self.draw_text_centered(
            x=self.width // 2,
            y=self.height // 2,
            text="PRESS ANY KEY TO START",
            font=self._text_font,
            color=(255, 255, 255),
        )

        self.draw_text_centered(
            x=self.width // 2,
            y=self.height // 2 + 50,
            text="COPYRIGHT © 2025 GLEN BEANE",
            font=self._text_font,
            color=(128, 128, 128),
        )

    def clear(self, color: tuple[int, int, int] = (0, 0, 0)) -> None:
        """Clear the frame buffer."""
        self._frame_buffer[:, :] = color
