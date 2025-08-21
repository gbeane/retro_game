from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QSoundEffect


class SFXPool(QObject):
    """
    SFXPool is a pool for playing overlapping sound effects (SFX) in the Pixel Blaster game.

    TODO - Allow each sound effect to have multiple variations.
    """

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._sfx: dict[str, list[QSoundEffect]] = {}
        self._idx: dict[str, int] = {}

    def add_effect(self, name: str, path: Path, pool_size: int = 1, volume: float = 0.8) -> None:
        """
        Add a sound effect to the pool.

        Args:
            name (str): The name of the sound effect.
            path (Path): The file path to the sound effect.
            pool_size (int): The number of instances of this sound effect to create.
            volume (float): The volume level for the sound effect, default is 0.8.
        """
        pool: list[QSoundEffect] = []

        for _ in range(pool_size):
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(path.absolute()))
            effect.setLoopCount(1)
            effect.setVolume(volume)
            pool.append(effect)
        self._sfx[name] = pool
        self._idx[name] = 0

    def has_effect(self, name: str) -> bool:
        """Check if a sound effect exists in the pool."""
        return name in self._sfx

    def set_volume(self, name: str, volume: float) -> None:
        """Set volume for all pooled players of an effect."""
        for sfx in self._sfx.get(name, []):
            sfx.setVolume(volume)

    def play(self, name: str) -> None:
        """Play a sound effect from the pool.

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

    def stop(self, name: str | None = None) -> None:
        """Stop playing a sound effect or all sound effects if no name is provided.

        Args:
            name (str | None): The name of the sound effect to stop. If None, stops all effects.
        """
        if name is None:
            for pool in self._sfx.values():
                for effect in pool:
                    effect.stop()
        else:
            pool = self._sfx.get(name)
            if pool:
                for effect in pool:
                    effect.stop()
