# ShredTiles

A Piano Tiles–style rhythm game that turns your real guitar into a game controller. Notes scroll down lanes and you play them by picking the correct string on your guitar — detected via MIDI or microphone audio.

## Features

- **MIDI input** — plug in a USB MIDI interface and play notes to hit tiles
- **Audio pitch detection** — use a microphone; autocorrelation + parabolic interpolation for accurate note tracking
- **Audio monitoring** — hear your guitar through speakers/headphones in real-time while playing (full-duplex callback stream, low latency)
- **Built-in chromatic tuner** — tune your guitar before playing, with visual cents meter
- **Track/channel selection** — pick which MIDI track and channel to play
- **Tile deduplication** — same-lane notes within 100ms are merged so strummed chords don't break your combo
- **Slide auto-hit** — nearby notes on adjacent lanes auto-register when you hit a note, simulating legato/slides
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

MIDI notes map to lanes as `(note - 40) % 6`. Audio pitch detection uses autocorrelation with parabolic interpolation on 1024-sample blocks. When using audio input mode, the game plays your guitar through your speakers in real-time via a callback-based full-duplex stream with 60% monitor gain — no synthetic tones, just your instrument.

### Tips for audio input

- Use **headphones** to avoid feedback between speakers and microphone
- Keep your guitar close to the mic and adjust system input volume so the level is clear but not clipping
- The tuner screen also uses audio monitoring — tune while hearing yourself

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
