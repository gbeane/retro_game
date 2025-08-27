from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class LoopedSFX(QObject):
    """Class to manage looped sound effect using QMediaPlayer and QAudioOutput."""

    def __init__(self, path: Path, parent: QObject = None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.player.setPlaybackRate(1.0)
        self.audio_output.setVolume(0.0)

    def play(self):
        """Start playing the looped sound effect."""
        self.player.play()

    def stop(self):
        """Stop playing the looped sound effect."""
        self.player.stop()

    @property
    def playback_rate(self) -> float:
        """Get the current playback rate of the sound effect."""
        return self.player.playbackRate()

    @playback_rate.setter
    def playback_rate(self, rate: float):
        """Set the playback rate of the sound effect.

        Args:
            rate: A float where 1.0 is normal speed, 0.5 is half speed, and 2.0 is double speed.
        """
        self.player.setPlaybackRate(rate)

    @property
    def playing(self) -> bool:
        """Check if the sound effect is currently playing."""
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    @property
    def volume(self) -> float:
        """Get the current volume of the sound effect."""
        return self.audio_output.volume()

    @volume.setter
    def volume(self, volume: float):
        """Set the volume of the sound effec.

        Args:
            volume: A float between 0.0 (mute) and 1.0 (max volume).
        """
        self.audio_output.setVolume(max(0.0, min(1.0, volume)))
