# ShredTiles

A Piano Tiles–style rhythm game that turns your real guitar into a game controller. Notes scroll down lanes and you play them by picking the correct string on your guitar — detected via MIDI or microphone audio.

## Features

- **MIDI input** — plug in a USB MIDI interface and play notes to hit tiles
- **Audio pitch detection** — use a microphone; autocorrelation + parabolic interpolation for accurate note tracking
- **Built-in chromatic tuner** — tune your guitar before playing, with visual cents meter
- **Track/channel selection** — pick which MIDI track and channel to play
- **3-2-1-GO countdown** before gameplay starts
- **Pause / Resume** — press `ESC` during gameplay
- **Restart** — press `R` while paused to replay the same track
- **Back to menu** — press `B` while paused to return to the title screen
- **Score, combo, rating system** with perfect/good/ok timing windows
- **Speed adjustment** — hold `UP`/`DOWN` during gameplay to change scroll speed

## Controls

| Key | Action |
|---|---|
| `1`–`6` | Hit lane (keyboard mode) |
| Mouse click | Hit lane under cursor |
| `ESC` | Pause / resume |
| `R` (paused) | Restart track |
| `B` / `M` (paused) | Back to menu |
| `UP` / `DOWN` | Increase / decrease scroll speed |

## MIDI / Audio input

MIDI notes map to lanes as `(note - 40) % 6`. Audio pitch detection uses autocorrelation on 2048-sample blocks at the device's default sample rate.

## Requirements

- Python 3.10+
- pygame 2.x
- mido
- numpy
- sounddevice (for audio input)

## Running

```bash
python main.py <midi-file>
```

Or from the source directory:

```bash
cd src && python ../main.py ../data/midi/your-song.mid
```
