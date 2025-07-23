"""
main_window.py

Pixel Blaster
Copyright (c) 2025 Glen Beane
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow

from .game_widget import GameWidget


class MainWindow(QMainWindow):
    """MainWindow class for the Pixel Blaster game."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Blaster")
        self.game_widget = GameWidget(self)
        self.setCentralWidget(self.game_widget)
        self.game_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.game_widget.setFocus()
        self.aspect_ratio = (
            self.game_widget.sizeHint().width() / self.game_widget.sizeHint().height()
        )
        self.resize(self.game_widget.sizeHint())

    def resizeEvent(self, event):
        """Handle the resize event to maintain aspect ratio."""
        new_width = event.size().width()
        new_height = int(new_width / self.aspect_ratio)
        if new_height > event.size().height():
            new_height = event.size().height()
            new_width = int(new_height * self.aspect_ratio)
        self.resize(new_width, new_height)
        super().resizeEvent(event)
