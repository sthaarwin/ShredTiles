from __future__ import annotations

import math
import struct
import warnings

import pygame


NOTE_DURATION_MS = 180
SAMPLE_RATE = 22050
VOLUME = 0.15


def _midi_to_freq(note: int) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def _generate_sine(note: int) -> pygame.mixer.Sound:
    freq = _midi_to_freq(note)
    n_samples = int(SAMPLE_RATE * NOTE_DURATION_MS / 1000)
    samples = []

    for i in range(n_samples):
        t = i / SAMPLE_RATE
        # Sine wave with a quick fade-out envelope to avoid clicks
        envelope = 1.0 - (i / n_samples) ** 3
        value = int(VOLUME * 32767 * math.sin(2 * math.pi * freq * t) * envelope)
        samples.append(max(-32768, min(32767, value)))

    buf = struct.pack(f"<{n_samples}h", *samples)
    return pygame.mixer.Sound(buffer=buf)


class SoundEngine:
    def __init__(self):
        self._sounds: dict = {}
        self.enabled = False

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
                self.enabled = True
            except Exception:
                self.enabled = False

    def preload_range(self, low: int, high: int):
        if not self.enabled:
            return
        for note in range(low, high + 1):
            if note not in self._sounds:
                self._sounds[note] = _generate_sine(note)

    def play_note(self, note: int):
        if not self.enabled:
            return
        if note not in self._sounds:
            self._sounds[note] = _generate_sine(note)
        self._sounds[note].play()
