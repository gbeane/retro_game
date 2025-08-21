"""
entrypoint.py

Pixel Blaster
Copyright (c) 2025 Glen Beane

This module serves as the main entry point for the Pixel Blaster game. Installing the package will create a
command-line script in the Python environment's path that launches the game by calling the `main` function
in this module. You cn also invoke this module directly to run the game.
"""
import os

from PySide6.QtWidgets import QApplication

from .ui import MainWindow


def main():
    """Main entrypoint for the Retro Asteroids game."""

    os.environ["QT_LOGGING_RULES"] = "*.debug=false;*.info=false"

    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
