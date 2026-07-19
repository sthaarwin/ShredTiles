from __future__ import annotations

import sys
from collections import defaultdict

import mido

from src.tile import Tile

GM_INSTRUMENTS = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavinet",
    "Celesta", "Glockenspiel", "Music Box", "Vibraphone",
    "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ",
    "Reed Organ", "Accordion", "Harmonica", "Tango Accordion",
    "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)", "Electric Guitar (clean)",
    "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar", "Guitar Harmonics",
    "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2",
    "Violin", "Viola", "Cello", "Contrabass",
    "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani",
    "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2",
    "Choir Aahs", "Voice Oohs", "Synth Choir", "Orchestra Hit",
    "Trumpet", "Trombone", "Tuba", "Muted Trumpet",
    "French Horn", "Brass Section", "Synth Brass 1", "Synth Brass 2",
    "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax",
    "Oboe", "English Horn", "Bassoon", "Clarinet",
    "Piccolo", "Flute", "Recorder", "Pan Flute",
    "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)",
    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass+lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)",
    "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)",
    "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",
    "Sitar", "Banjo", "Shamisen", "Koto",
    "Kalimba", "Bagpipe", "Fiddle", "Shanai",
    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock",
    "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal",
    "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet",
    "Telephone Ring", "Helicopter", "Applause", "Gunshot",
]


def _instrument_name(program: int) -> str:
    if 0 <= program < len(GM_INSTRUMENTS):
        return GM_INSTRUMENTS[program]
    return "Unknown"


def _detect_programs(track) -> dict[int, int]:
    prog_map: dict[int, int] = {}
    for msg in track:
        if msg.type == "program_change":
            prog_map[msg.channel] = msg.program
    return prog_map


def _group_notes_by_channel(track) -> dict[int, list]:
    channels: dict[int, list] = defaultdict(list)
    tick = 0
    for msg in track:
        tick += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            ch = getattr(msg, "channel", 0)
            channels[ch].append((tick, msg))
    return dict(channels)


def select_midi_port() -> str | None:
    try:
        ports = mido.get_input_names()
    except Exception:
        ports = []

    if not ports:
        print("  No MIDI input devices detected.")
        print("  Use keyboard (1-6) or mouse to play.")
        print("=" * 50)
        return None

    print("  MIDI input ports:")
    for i, name in enumerate(ports):
        print(f"  [{i}] {name}")
    print("  [n] None (use keyboard/mouse)")
    print("=" * 50)

    while True:
        choice = input(f"  Pick MIDI port [0-{len(ports)-1} or n]: ").strip().lower()
        if choice == "n":
            return None
        try:
            idx = int(choice)
            if 0 <= idx < len(ports):
                return ports[idx]
        except ValueError:
            pass
        print("  Invalid choice.")

    return None


def load_midi(file_path: str) -> list[Tile]:
    try:
        mid = mido.MidiFile(file_path)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("  SHREDTILES — MIDI SELECTOR")
    print("=" * 50)

    ticks_per_beat = mid.ticks_per_beat

    tempo_events: list[tuple[int, int]] = []
    tick_acc = 0
    for msg in mid.tracks[0]:
        tick_acc += msg.time
        if msg.type == "set_tempo":
            tempo_events.append((tick_acc, msg.tempo))

    target_track_index: int | None = None
    filter_channel: int | None = None

    if mid.type == 0:
        track = mid.tracks[0]
        channels = _group_notes_by_channel(track)
        programs = _detect_programs(track)

        if len(channels) == 1:
            ch = list(channels.keys())[0]
            prog = programs.get(ch, -1)
            name = _instrument_name(prog) if prog >= 0 else f"Channel {ch}"
            count = len(channels[ch])
            print(f"  Using channel {ch} — {name} ({count} notes)")
            target_track_index = 0
            filter_channel = ch
        else:
            print("  Channels found:")
            sorted_chs = sorted(channels.keys())
            for ch in sorted_chs:
                prog = programs.get(ch, -1)
                label = _instrument_name(prog) if prog >= 0 else f"Channel {ch}"
                count = len(channels[ch])
                print(f"  [{ch:>2}] {label:<35} ({count} notes)")
            print("  [a] All channels")
            print("=" * 50)

            while True:
                choice = input(f"  Pick a channel [{', '.join(map(str, sorted_chs))} or a]: ").strip().lower()
                if choice == "a":
                    target_track_index = 0
                    filter_channel = None
                    break
                try:
                    ch = int(choice)
                    if ch in channels:
                        target_track_index = 0
                        filter_channel = ch
                        break
                except ValueError:
                    pass
                print("  Invalid choice.")
    else:
        valid_tracks = []
        for i, trk in enumerate(mid.tracks):
            note_count = sum(1 for m in trk if m.type == "note_on" and m.velocity > 0)
            label = trk.name or f"Track {i}"
            print(f"  [{i}] {label:<35} ({note_count} notes)")
            if note_count > 0:
                valid_tracks.append(i)

        if not valid_tracks:
            print("  No note data found in this file.")
            sys.exit(1)

        print("=" * 50)
        while True:
            try:
                choice = input(f"  Pick a track [{', '.join(map(str, valid_tracks))}]: ")
                target_track_index = int(choice)
                if target_track_index in valid_tracks:
                    break
            except ValueError:
                pass
            print("  Invalid choice.")

    tiles = parse_midi_tracks(mid, target_track_index, filter_channel)
    print(f"\n  Loaded {len(tiles)} notes")
    print("=" * 50 + "\n")
    return tiles


def parse_midi_tracks(mid: mido.MidiFile, track_index: int, filter_channel: int | None = None) -> list[Tile]:
    ticks_per_beat = mid.ticks_per_beat

    tempo_events: list[tuple[int, int]] = []
    tick_acc = 0
    for msg in mid.tracks[0]:
        tick_acc += msg.time
        if msg.type == "set_tempo":
            tempo_events.append((tick_acc, msg.tempo))

    tempo_index = 0
    current_tempo = 500_000
    tiles: list[Tile] = []
    track_tick = 0

    for msg in mid.tracks[track_index]:
        track_tick += msg.time

        while tempo_index < len(tempo_events) and track_tick >= tempo_events[tempo_index][0]:
            current_tempo = tempo_events[tempo_index][1]
            tempo_index += 1

        ms_per_tick = (current_tempo / 1000.0) / ticks_per_beat
        time_ms = track_tick * ms_per_tick

        if msg.type == "note_on" and msg.velocity > 0:
            if filter_channel is not None and getattr(msg, "channel", 0) != filter_channel:
                continue
            lane = (msg.note - 40) % 6
            tiles.append(Tile(lane=lane, fret=msg.note, spawn_time=time_ms, channel=getattr(msg, "channel", 0)))

    return tiles
