from __future__ import annotations

import queue

import pygame

from src.config import FPS, SCREEN_WIDTH, SCREEN_HEIGHT
from src.renderer import Renderer
from src.screens import (
    MainMenu, TrackSelectScreen, InputSelectScreen,
    TunerScreen, GameplayScreen, ResultsScreen,
)
from src.midi_loader import _group_notes_by_channel, _detect_programs, _instrument_name, parse_midi_tracks
from src.sound_engine import SoundEngine


class App:
    def __init__(self, midi_file: str, mid_data):
        self.midi_file = midi_file
        self.mid = mid_data

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ShredTiles")
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.running = True

        self.tiles = []
        self.input_cfg = {"type": "none"}
        self.selected_channel = None
        self.selected_track_index = 0
        self._track_options = []

        self.sound = SoundEngine()
        self.note_queue: queue.Queue = queue.Queue()
        self.audio_input = None

        self._build_track_options()

        self.screens = {
            "menu": MainMenu(self),
            "track_select": TrackSelectScreen(self),
            "input_select": InputSelectScreen(self),
            "tuner": TunerScreen(self),
            "gameplay": GameplayScreen(self),
            "results": ResultsScreen(self),
        }
        self.current = "menu"
        self._enter_screen("menu")

    def _build_track_options(self):
        import mido
        mid = self.mid
        options = []

        for i, trk in enumerate(mid.tracks):
            note_count = sum(1 for m in trk if m.type == "note_on" and m.velocity > 0)
            if note_count > 0:
                label = trk.name or f"Track {i}"
                options.append({
                    "key": i, "label": label, "count": note_count,
                    "track_index": i, "channel": None,
                })

        if mid.type == 0 and len(options) <= 1 and options:
            trk = mid.tracks[0]
            channels = _group_notes_by_channel(trk)
            programs = _detect_programs(trk)
            if len(channels) > 1:
                options = []
                sorted_chs = sorted(channels.keys())
                for ch in sorted_chs:
                    prog = programs.get(ch, -1)
                    label = _instrument_name(prog) if prog >= 0 else f"Channel {ch}"
                    options.append({
                        "key": ch, "label": label, "count": len(channels[ch]),
                        "track_index": 0, "channel": ch,
                    })
                options.append({
                    "key": "a", "label": "All channels", "count": sum(len(v) for v in channels.values()),
                    "track_index": 0, "channel": None,
                })

        self._track_options = options

    def _enter_screen(self, name):
        screen = self.screens.get(name)
        if screen and hasattr(screen, "enter"):
            screen.enter()

    def _load_tiles(self):
        self.tiles = parse_midi_tracks(
            self.mid,
            self.selected_track_index,
            self.selected_channel,
        )

    def _init_audio_engine(self):
        if self.sound.enabled and self.tiles:
            frets = {t.fret for t in self.tiles}
            if frets:
                self.sound.preload_range(min(frets), max(frets))

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                screen = self.screens.get(self.current)
                if screen:
                    result = screen.handle_event(event)
                    if result and result != self.current:
                        if hasattr(screen, "_leave"):
                            screen._leave()
                        self.current = result
                        self._enter_screen(result)
                        break

            screen = self.screens.get(self.current)
            if screen:
                screen.update(dt)
                screen.render()

            pygame.display.flip()

        pygame.quit()
