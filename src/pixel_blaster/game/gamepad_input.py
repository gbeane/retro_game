import enum
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
from PySide6.QtCore import QObject, QTimer

from pixel_blaster.constants import REPEAT_TIMER_INTERVAL


class GamepadInput(QObject):
    """Pygame-backed joystick/gamepad adapter

    Feeds to existing keyboard-based input API:
      game.handle_key(Game.Key.*, pressed: bool).

    This was developed/tested with a Hyperkin "Trooper 2" USB controller.
    This controller shows as having 8 buttons and 2 axis. The controls are:
        B0: left primary button
        B1: right primary button
        B2: <no physical button>
        B3: <no physical button>
        B4: Select (front left)
        B5: Start (front right)
        B6: LB (rear left)
        B7: RB (rear right)
        Axis 0: left (negative) / right (positive)
        Axis 1: up (negative) / down (positive)

    Mappings to game keyboard controls:
      - stick axis 0 -> LEFT / RIGHT (with deadzone)
      - stick axis 1 -> UP (with deadzone). Game does not currently use DOWN control.
      - Buttons 0 or 1        -> FIRE
      - Select (4), Start (5) -> ENTER

    Note: For keyboard controls, left/right turns use a fixed repeat timer interval while the key is held.
      Mirror that behavior for the gamepad: once the stick passes the DEADZONE, treat it as held.

    TODO: implement a more flexible solution that can be configured/mapped
      for different controllers and layouts.
    """

    DEADZONE = 0.10  # stick must move this far to register

    class Input(enum.IntEnum):
        """Logical game inputs we track from the gamepad."""
        LEFT = enum.auto()
        RIGHT = enum.auto()
        UP = enum.auto()
        DOWN = enum.auto()
        FIRE = enum.auto()
        START = enum.auto()

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game

        # Init pygame joystick subsystem
        pygame.init()
        pygame.joystick.init()

        self._joysticks: list[pygame.joystick.Joystick] = []
        self._refresh_joysticks()

        # State tracking so we only send changes
        self._input_states = dict.fromkeys(self.Input, False)

        # Repeat timers for LEFT/RIGHT (mirror keyboard behavior)
        self.left_repeat_timer = QTimer(self)
        self.left_repeat_timer.setInterval(REPEAT_TIMER_INTERVAL)
        self.left_repeat_timer.timeout.connect(
            lambda: self.game.handle_key(self.game.Key.LEFT, True)
        )
        self.right_repeat_timer = QTimer(self)
        self.right_repeat_timer.setInterval(REPEAT_TIMER_INTERVAL)
        self.right_repeat_timer.timeout.connect(
            lambda: self.game.handle_key(self.game.Key.RIGHT, True)
        )

        # timer used to poll pygame for joystick state and emit key events as needed
        # Poll at ~60 Hz
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._poll)
        self._timer.start()

    @property
    def joystick_enabled(self) -> bool:
        """Returns True if at least one joystick/gamepad is connected."""
        return len(self._joysticks) > 0

    def cleanup(self) -> None:
        """Cleanup resources

        (call on app exit by connecting to QApplication.aboutToQuit() signal).
        """
        if self._timer.isActive():
            self._timer.stop()
        if self.right_repeat_timer.isActive():
            self.left_repeat_timer.stop()
        if self.left_repeat_timer.isActive():
            self.right_repeat_timer.stop()
        pygame.quit()

    def _refresh_joysticks(self) -> None:
        """Re-scan and re-initialize all connected joysticks."""
        self._joysticks.clear()
        for i in range(pygame.joystick.get_count()):
            try:
                j = pygame.joystick.Joystick(i)
                j.init()
                self._joysticks.append(j)
            except Exception:
                # Ignore devices that fail to init
                pass
        self.game.show_joystick_controls = self.joystick_enabled

    def _poll(self) -> None:
        """Poll joystick state and emit key events as needed."""
        try:
            # Keep pygame's event queue flowing
            pygame.event.pump()
        except Exception:
            return

        # Hot-plug handling: if count changed, refresh list
        if len(self._joysticks) != pygame.joystick.get_count():
            self._refresh_joysticks()

        if not self._joysticks:
            # Release any held states if no controller present
            for i in self.Input:
                self._handle_input_changed(i, False)
            return

        j = self._joysticks[0]  # use first controller

        # left/right from axis 0
        x = j.get_axis(0)
        left = x < -self.DEADZONE
        right = x > self.DEADZONE

        # Emit left/right changes
        self._handle_input_changed(self.Input.LEFT, left)
        self._handle_input_changed(self.Input.RIGHT, right)

        # up/down from axis 1
        y = j.get_axis(1)
        up_axis = y < -self.DEADZONE
        down_axis = y > self.DEADZONE

        # Emit up/down directly from axis
        self._handle_input_changed(self.Input.UP, up_axis)
        self._handle_input_changed(self.Input.DOWN, down_axis)

        # buttons
        # currently, we just use button 0 or 1 for fire, and buttons 4 or 5 for enter
        nb = j.get_numbuttons()
        fire = (nb >= 1 and j.get_button(0)) or (nb >= 2 and j.get_button(1))
        enter = (nb >= 4 and j.get_button(4)) or (nb >= 5 and j.get_button(5))
        self._handle_input_changed(self.Input.FIRE, bool(fire))
        self._handle_input_changed(self.Input.START, bool(enter))

    def _handle_input_changed(self, which: "GamepadInput.Input", value: bool) -> None:
        prev = self._input_states.get(which, False)
        if value != prev:
            self._input_states[which] = value
            if which == self.Input.LEFT:
                self.game.handle_key(self.game.Key.LEFT, value)
                if value:
                    self.left_repeat_timer.start()
                else:
                    self.left_repeat_timer.stop()
            elif which == self.Input.RIGHT:
                self.game.handle_key(self.game.Key.RIGHT, value)
                if value:
                    self.right_repeat_timer.start()
                else:
                    self.right_repeat_timer.stop()
            elif which == self.Input.UP:
                self.game.handle_key(self.game.Key.UP, value)

            elif which == self.Input.FIRE:
                self.game.handle_key(self.game.Key.FIRE, value)
            elif which == self.Input.START:
                self.game.handle_key(self.game.Key.ENTER, value)
