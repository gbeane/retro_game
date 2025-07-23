# Pixel Blaster

by Glen Beane

Pixel Blaster is a simple retro-style asteroid blaster game built with Python, PySide6, and Numpy. The game is inspired
by classic arcade games and aims to provide a nostalgic gaming experience. It is not an exact clone but is inspired by
the gameplay and aesthetics of Asteroids on the Atari 2600. It has been decades since I played that game using an 
emulator in the early 2000s, so this is based on distant memories.

This is a work in progress, and the game is not yet complete. 

## Design

While the game is implemented using PySide6, I make minimal use of the Qt framework. Primarily, I use it for window 
management, keyboard input, and the timer-based game loop. The game graphics themselves are implemented using a
frame-buffer approach, which is implemented with a Numpy array. Pixels are drawn directly to the frame buffer, and 
the display is updated by converting the Numpy array to a QImage and displaying it in a QLabel.

## Current Features
- Player-controlled spaceship
- Bitmapped font for displaying score and player lives
