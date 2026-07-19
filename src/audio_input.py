from __future__ import annotations

import queue
import threading

import numpy as np

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
MIN_FREQ = 75.0
MAX_FREQ = 1200.0
RMS_THRESHOLD = 0.008
SILENCE_FRAMES_RESET = 8


def freq_to_midi_float(freq: float) -> float | None:
    if freq <= 0 or not np.isfinite(freq):
        return None
    return 12 * np.log2(freq / 440.0) + 69


def freq_to_midi(freq: float) -> int:
    v = freq_to_midi_float(freq)
    if v is None:
        return -1
    return int(round(v))


def detect_pitch(audio: np.ndarray, sr: int) -> tuple[int, float, float]:
    audio = audio - np.mean(audio)
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < RMS_THRESHOLD:
        return -1, 0.0, rms

    n = len(audio)
    corr = np.correlate(audio, audio, mode="full")
    corr = corr[n - 1:]

    min_lag = max(int(sr / MAX_FREQ), 1)
    max_lag = min(int(sr / MIN_FREQ), len(corr) - 1)
    if min_lag >= max_lag:
        return -1, 0.0, rms

    search = corr[min_lag:max_lag + 1]
    peak_idx = int(np.argmax(search)) + min_lag

    peak_val = corr[peak_idx]
    if peak_val < 0.15 * corr[0]:
        return -1, 0.0, rms

    if 1 < peak_idx < len(corr) - 1:
        a, b, c = corr[peak_idx - 1], corr[peak_idx], corr[peak_idx + 1]
        denom = a - 2 * b + c
        if abs(denom) > 1e-12:
            delta = 0.5 * (a - c) / denom
            refined_lag = peak_idx + delta
        else:
            refined_lag = float(peak_idx)
    else:
        refined_lag = float(peak_idx)

    if not (1 < refined_lag < len(corr)):
        return -1, 0.0, rms

    freq = sr / refined_lag
    midi_float = freq_to_midi_float(freq)
    if midi_float is None:
        return -1, 0.0, rms

    note = int(round(midi_float))
    expected_freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
    cents = 1200.0 * np.log2(freq / expected_freq)

    return note, cents, rms


def list_audio_devices() -> list[tuple[int, str]]:
    import sounddevice as sd
    devices = []
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            devices.append((i, dev["name"]))
    return devices


class AudioPitchDetector:
    def __init__(self, monitor: bool = False):
        self.queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._running = False
        self._last_note = -1
        self._silent = 0
        self.monitor = monitor

    def start(self, device: int | None = None):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, args=(device,), daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self, device: int | None):
        import sounddevice as sd
        try:
            try:
                info = sd.query_devices(device)
                sr = int(info["default_samplerate"]) if info and info.get("default_samplerate") else SAMPLE_RATE
            except Exception:
                sr = SAMPLE_RATE

            dev = (device, None) if self.monitor else device

            def callback(indata, outdata, frames, _time, status):
                if status:
                    return
                if self.monitor:
                    outdata[:] = indata * 0.6
                note, cents, rms = detect_pitch(indata.flatten(), sr)
                if note >= 0:
                    if note != self._last_note or self._silent > SILENCE_FRAMES_RESET:
                        self.queue.put(("note", note, cents))
                        self._last_note = note
                        self._silent = 0
                else:
                    self._silent += 1
                    if self._silent > SILENCE_FRAMES_RESET * 3:
                        self._last_note = -1

            with sd.Stream(
                device=dev,
                channels=1,
                samplerate=sr,
                blocksize=BLOCK_SIZE,
                callback=callback,
            ):
                while self._running:
                    sd.sleep(100)
        except Exception as e:
            print(f"\n  Audio input error: {e}")
