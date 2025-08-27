from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtMultimedia import QSoundEffect

from .looped_sfx import LoopedSFX


class SFXPool(QObject):
    """
    SFXPool is a pool for playing overlapping sound effects (SFX) in the Pixel Blaster game.

    Todo:
      - Allow each sound effect to have multiple variations.
    """

    _TARGET_LOOPED_VOLUME = 0.6  # Default target volume for looped sound effects
    _DEFAULT_VOLUME = 0.8  # Default volume for one-shot sound effects

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        # one-shot sound effects pool
        self._sfx: dict[str, list[QSoundEffect]] = {}
        self._idx: dict[str, int] = {}  # index used to round robin through the pool

        # looped sound effects
        self._looped_sfx: dict[str, LoopedSFX] = {}
        self._loop_fade_target: dict[str, float] = {}  # target volume for fading
        self._loop_fade_timers: dict[str, QTimer] = {}  # timers for fading
        self._loop_fade_step: dict[str, float] = {}  # volume change per timer tick
        self._loop_rate_timers: dict[str, QTimer] = {}  # timers for changing playback rate
        self._loop_rate_step: dict[str, float] = {}  # playback rate change per timer tick
        self._loop_rate_target: dict[str, float] = {}  # target playback rate for changing

    def add_effect(
        self, name: str, path: Path, pool_size: int = 1, volume: float | None = None
    ) -> None:
        """Add a one-shot sound effect to the pool.

        Args:
            name (str): The name of the sound effect.
            path (Path): The file path to the sound effect.
            pool_size (int): The number of instances of this sound effect to create.
            volume (float): The volume level for the sound effect, default is 0.8.

        Note: currently names must be unique across both one-shot and looped effects.
        """
        if name in self._sfx or name in self._looped_sfx:
            return

        if not path.exists():
            raise FileNotFoundError(f"Sound effect file not found: {path}")

        if volume is None:
            volume = self._DEFAULT_VOLUME

        pool: list[QSoundEffect] = []

        for _ in range(pool_size):
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(path.absolute()))
            effect.setLoopCount(1)
            effect.setVolume(volume)
            pool.append(effect)
        self._sfx[name] = pool
        self._idx[name] = 0

    def add_looped_effect(self, name: str, path: Path) -> None:
        """
        Add a looped sound effect to the pool.

        Args:
            name (str): The name of the sound effect.
            path (Path): The file path to the sound effect.

        Note: Names must be unique across both one-shot and looped effects.
        """
        if name in self._looped_sfx or name in self._sfx:
            return

        if not path.exists():
            raise FileNotFoundError(f"Looped sound effect file not found: {path}")

        effect = LoopedSFX(path, self)
        self._looped_sfx[name] = effect

        self._loop_fade_target[name] = self._TARGET_LOOPED_VOLUME
        self._loop_fade_timers[name] = QTimer(self)
        self._loop_fade_timers[name].setInterval(16)  # ~60 FPS
        self._loop_fade_timers[name].timeout.connect(lambda n=name: self._on_loop_fade(n))
        self._loop_fade_step[name] = 0.0

        self._loop_rate_timers[name] = QTimer(self)
        self._loop_rate_timers[name].setInterval(128)
        self._loop_rate_timers[name].timeout.connect(lambda n=name: self._on_loop_rate_change(n))
        self._loop_rate_step[name] = 0.0

    def has_effect(self, name: str) -> bool:
        """Check if a sound effect exists in the pool."""
        return name in self._sfx or name in self._looped_sfx

    def set_volume(self, name: str, volume: float) -> None:
        """Set volume for an effect."""
        # handle one-shot effects
        for sfx in self._sfx.get(name, []):
            sfx.setVolume(volume)

        # handle looped effects
        if name in self._looped_sfx:
            self._looped_sfx[name].volume = max(0.0, min(1.0, volume))

    def set_playback_rate(self, name: str, rate: float, duration: int = 0) -> None:
        """Set playback rate for a looped effect.

        Args:
            name (str): The name of the looped sound effect.
            rate (float): The playback rate where 1.0 is normal speed, 0.5 is half speed, and 2.0 is double speed.
            duration (int): The duration in milliseconds over which to change the playback rate. If 0, changes immediately.
        """
        if name in self._looped_sfx:
            if duration > 0:
                self._loop_rate_target[name] = rate
                interval = self._loop_rate_timers[name].interval()
                steps = max(1, duration // interval)
                self._loop_rate_step[name] = (rate - self._looped_sfx[name].playback_rate) / steps
                self._loop_rate_timers[name].start()
            else:
                self._looped_sfx[name].playback_rate = rate

    def play(self, name: str) -> None:
        """Play a one-shot sound effect from the pool.

        Args:
            name (str): The name of the sound effect to play.

        Does nothing if the effect does not exist in the pool.
        """
        pool = self._sfx.get(name)
        if not pool:
            return

        i = self._idx[name]
        effect = pool[i]
        self._idx[name] = (i + 1) % len(pool)

        effect.play()

    def play_looped(
        self, name: str, volume: float | None = None, fade_duration: int = 150
    ) -> None:
        """Play a looped sound effect with a fade-in.

        Args:
            name (str): The name of the looped sound effect to play.
            volume (float | None): The volume to set for the looped sound effect. If None, uses the default target volume.
            fade_duration (int): The duration of the fade-in in milliseconds.

        Sound will fade in from 0 volume to the target volume over the specified duration, and then will
        loop indefinitely until stopped.
        """
        if name not in self._looped_sfx:
            return

        if volume is None:
            volume = self._TARGET_LOOPED_VOLUME

        effect = self._looped_sfx[name]
        if not effect.playing:
            effect.volume = 0.0  # start at 0 volume, will fade up to target volume
            effect.play()
        self._fade_loop_to(name, volume, fade_duration)

    def stop_loop(self, name: str, fade_duration: int = 150) -> None:
        """Stop a looped sound effect with a fade-out.

        Args:
            name (str): The name of the looped sound effect to stop.
            fade_duration (int): The duration of the fade-out in milliseconds.
        """
        if name not in self._looped_sfx:
            return

        self._fade_loop_to(name, 0.0, fade_duration)

    def _fade_loop_to(self, name: str, target: float, fade_duration: int) -> None:
        """Fade a looped sound effect to a target volume over a specified duration.

        Args:
            name (str): The name of the looped sound effect.
            target (float): The target volume to fade to (0.0 to 1.0).
            fade_duration (int): The duration of the fade in milliseconds.
        """
        effect = self._looped_sfx.get(name)
        timer = self._loop_fade_timers.get(name)
        if not effect or not timer:
            return

        current = effect.volume
        steps = max(
            1, fade_duration // timer.interval()
        )  # number of steps it will take to reach target
        self._loop_fade_step[name] = (
            target - current
        ) / steps  # how much to change the volume each step

        # save the target volume for later
        self._loop_fade_target[name] = target

        timer.start()

    def _on_loop_fade(self, name: str) -> None:
        """Handle the fading of looped sound effects.

        Args:
            name (str): The name of the looped sound effect being faded.

        This is called periodically by a QTimer to adjust the volume of the effect over a specified duration to fade
        the sound in or out.
        """
        effect = self._looped_sfx.get(name)
        timer = self._loop_fade_timers.get(name)
        if not effect or not timer:
            return

        # calculate the new volume based on the step
        v = effect.volume + self._loop_fade_step[name]

        # have we reached the target volume?
        target = self._loop_fade_target[name]
        done = (self._loop_fade_step[name] >= 0 and v >= target) or (
            self._loop_fade_step[name] < 0 and v <= target
        )

        # if done fading in or out, set volume to target and stop the timer.
        if done:
            v = target
            timer.stop()

            # if the target volume is 0, stop the effect
            if v <= 0.0:
                effect.stop()

        effect.volume = max(0.0, min(1.0, v))

    def _on_loop_rate_change(self, name: str) -> None:
        """Handle changing the playback rate of a looped sound effect over time.

        Args:
            name (str): The name of the looped sound effect being adjusted.

        This is called periodically by a QTimer to adjust the playback rate of the effect over a specified duration.
        """
        effect = self._looped_sfx.get(name)
        timer = self._loop_rate_timers.get(name)
        if not effect or not timer:
            return

        # calculate the new playback rate based on the step
        r = effect.playback_rate + self._loop_rate_step[name]

        # have we reached the target playback rate?
        target = self._loop_rate_target[name]
        done = (self._loop_rate_step[name] >= 0 and r >= target) or (
            self._loop_rate_step[name] < 0 and r <= target
        )

        # if done changing rate, set to target and stop the timer.
        if done:
            r = target
            timer.stop()

        effect.playback_rate = max(0.5, min(2.0, r))

    def stop(self, name: str | None = None) -> None:
        """Stop playing a sound effect or all sound effects if no name is provided.

        Args:
            name (str | None): The name of the sound effect to stop. If None, stops all effects.

        Can stop a looped effect or a one-shot effect.
        """
        if name is None:
            for pool in self._sfx.values():
                for effect in pool:
                    effect.stop()
            for effect in self._looped_sfx.values():
                effect.stop()
            for timer in self._loop_fade_timers.values():
                timer.stop()
        else:
            for effect in self._sfx.get(name, []):
                effect.stop()

            if name in self._looped_sfx:
                self._looped_sfx[name].stop()
            if name in self._loop_fade_timers:
                self._loop_fade_timers[name].stop()
