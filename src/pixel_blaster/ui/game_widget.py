"""
game_widget.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QImage, QKeyEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from pixel_blaster.game import Game


class GameWidget(QWidget):
    """
    GameWidget is a custom QWidget responsible for rendering the Pixel Blaster game and handling user input.

    This widget manages the game loop, draws the current game frame, and processes keyboard events for player control.
    It uses a QTimer to update the game state at a fixed interval, ensuring smooth gameplay at approximately 60 FPS.
    The widget also implements custom key repeat logic for left and right movement, allowing for precise control.

    Key Responsibilities:
    - Display the game frame by converting the game's NumPy frame buffer to a QImage and scaling it to fit the widget.
    - Handle keyboard input for player actions, including movement and splash screen dismissal.
    - Manage custom key repeat timers for left and right movement keys.
    - Provide a size hint based on the game's dimensions and a default scale factor.
    """

    _REPEAT_TIMER_INTERVAL = 25  # Interval for repeat key events in milliseconds
    _DEFAULT_SCALE = 5  # Default scale factor for the game display

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = Game()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # run game loop every 16ms (approximately ~60 FPS)

        # Custom repeat timers.
        # By using QTimer, we can control the repeat rate of key events rather than relying on the default
        # auto-repeat behavior of key events.
        self.left_repeat_timer = QTimer(self)
        self.left_repeat_timer.timeout.connect(lambda: self.game.handle_key(Game.Key.LEFT, True))
        self.right_repeat_timer = QTimer(self)
        self.right_repeat_timer.timeout.connect(lambda: self.game.handle_key(Game.Key.RIGHT, True))

    def sizeHint(self) -> QSize:
        """Provide a size hint for the widget based on the game dimensions."""
        return QSize(
            self.game.width * self._DEFAULT_SCALE,
            self.game.height * self._DEFAULT_SCALE,
        )

    def update_game(self) -> None:
        """Update the game state and repaint the widget."""
        self.game.update()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Handle the paint event to draw the game frame."""
        # Get the frame buffer (shape: height, width, 3)
        frame = self.game.frame_buffer
        height, width, _ = frame.shape

        # Convert NumPy array to QImage
        image = QImage(frame.data, width, height, 3 * width, QImage.Format.Format_RGB888)

        # Calculate scaled size maintaining aspect ratio
        widget_size = self.size()
        scale = min(widget_size.width() / width, widget_size.height() / height)
        scaled_width = int(width * scale)
        scaled_height = int(height * scale)

        # Center the image
        x = (widget_size.width() - scaled_width) // 2
        y = (widget_size.height() - scaled_height) // 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(
            x,
            y,
            image.scaled(
                scaled_width,
                scaled_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            ),
        )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.isAutoRepeat():
            return

        if event.key() == Qt.Key.Key_Left:
            self.game.handle_key(Game.Key.LEFT, True)
            self.left_repeat_timer.start(self._REPEAT_TIMER_INTERVAL)
        elif event.key() == Qt.Key.Key_Right:
            self.game.handle_key(Game.Key.RIGHT, True)
            self.right_repeat_timer.start(self._REPEAT_TIMER_INTERVAL)
        elif event.key() == Qt.Key.Key_Up:
            self.game.handle_key(Game.Key.UP, True)
        else:
            # for any other key, just let the game know a key was pressed but still allow default handling
            # this is specifically for the 'any' key handling to dismiss the splash screen
            self.game.handle_key(Game.Key.ANY, True)
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle key release events."""
        if event.isAutoRepeat():
            return

        if event.key() == Qt.Key.Key_Left:
            self.game.handle_key(Game.Key.LEFT, False)
            self.left_repeat_timer.stop()
        elif event.key() == Qt.Key.Key_Right:
            self.game.handle_key(Game.Key.RIGHT, False)
            self.right_repeat_timer.stop()
        elif event.key() == Qt.Key.Key_Up:
            self.game.handle_key(Game.Key.UP, False)
        else:
            super().keyReleaseEvent(event)
