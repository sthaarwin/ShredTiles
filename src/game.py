from __future__ import annotations

import threading
import queue

import pygame
import mido

from src.config import (
    FPS, SCREEN_WIDTH, SCREEN_HEIGHT, NUM_LANES, LANE_WIDTH, TARGET_Y, SCREEN_HEIGHT,
    HIT_WINDOW_PERFECT, HIT_WINDOW_GOOD, HIT_WINDOW_OK, HIT_WINDOW_MISS,
    SCORE_PERFECT, SCORE_GOOD, SCORE_OK, COMBO_MULTIPLIER_STEP, MAX_COMBO_MULTIPLIER,
)
from src.tile import Tile
from src.sound_engine import SoundEngine
from src.audio_input import AudioPitchDetector

LANE_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]
SLIDE_THRESHOLD = 150.0


class Game:
    def __init__(self, tiles: list[Tile], input_cfg: dict | None = None,
                 renderer=None, screen=None, clock=None, sound=None):
        self.tiles = tiles
        self.game_time = 0.0
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.hit_count = 0
        self.miss_count = 0
        self.speed = 1.0
        self.total_notes = len(tiles)
        self.finished_game = False
        self.show_results = False
        self.game_started = False
        self.rating_text = ""
        self.rating_timer = 0
        self.paused = False

        self.lane_flash = [0] * NUM_LANES
        self.input_label = ""
        self.input_active = False
        self.input_activity = 0
        self.last_note = -1
        self.note_timer = 0
        self.msg_count = 0

        if screen:
            self.screen = screen
        else:
            pygame.init()
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("ShredTiles")

        if clock:
            self.clock = clock
        else:
            self.clock = pygame.time.Clock()

        self._just_pressed: list[int] = []
        self._pressed_lanes: set[int] = set()

        from src.renderer import Renderer
        self.renderer = renderer or Renderer(self.screen)

        self.sound = sound or SoundEngine()
        if self.sound.enabled and tiles and not self._is_audio:
            frets = {t.fret for t in tiles}
            if frets:
                self.sound.preload_range(min(frets), max(frets))

        self.note_queue: queue.Queue = queue.Queue()
        self._is_audio = input_cfg.get("type") == "audio" if input_cfg else False
        self._setup_input(input_cfg or {})

    def _setup_input(self, cfg: dict):
        method = cfg.get("type", "none")

        if method == "midi":
            port = cfg.get("name", cfg.get("port", ""))
            self.input_label = f"MIDI: {port}"
            try:
                t = threading.Thread(target=self._midi_worker, args=(port,), daemon=True)
                t.start()
                self.input_active = True
            except Exception:
                self.input_label = "MIDI: error"

        elif method == "audio":
            device = cfg.get("device")
            name = cfg.get("name", f"device {device}")
            self.input_label = f"Audio: {name}"
            self._audio = AudioPitchDetector(monitor=True)
            self._audio.queue = self.note_queue
            self._audio.start(device)
            self.input_active = True

        else:
            self.input_label = "Keyboard/Mouse"

    def _midi_worker(self, port_name: str):
        try:
            with mido.open_input(port_name) as port:
                for msg in port:
                    if msg.type == "note_on" and msg.velocity > 0:
                        self.note_queue.put(("note", msg.note, 0))
                    else:
                        self.note_queue.put(("other", msg.type, 0))
        except Exception:
            self.input_active = False

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quit"

        if event.type == pygame.KEYDOWN:
            for lane, key in enumerate(LANE_KEYS):
                if event.key == key:
                    self._just_pressed.append(lane)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if TARGET_Y <= my <= SCREEN_HEIGHT:
                lane = mx // LANE_WIDTH
                if 0 <= lane < NUM_LANES:
                    self._just_pressed.append(lane)

        return None

    def update(self, dt):
        if self.show_results:
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.speed = min(2.0, self.speed + 0.02)
        if keys[pygame.K_DOWN]:
            self.speed = max(0.2, self.speed - 0.02)
        self._pressed_lanes = {lane for lane, k in enumerate(LANE_KEYS) if keys[k]}

        if not self.game_started:
            for tile in self.tiles:
                if tile.active:
                    tile.update_y(0)
            self._just_pressed.clear()
            return

        dt_scaled = dt * self.speed
        self.game_time += dt_scaled

        self._process_notes()

        for lane in self._just_pressed:
            self._try_hit_lane(lane)
        self._just_pressed.clear()

        self._check_misses()
        self._check_finished()

        for tile in self.tiles:
            if tile.active:
                tile.update_y(self.game_time)

        if self.rating_timer > 0:
            self.rating_timer -= 1
        else:
            self.rating_text = ""

        if self.input_activity > 0:
            self.input_activity -= 1
        if self.note_timer > 0:
            self.note_timer -= 1

        for i in range(NUM_LANES):
            if self.lane_flash[i] > 0:
                self.lane_flash[i] -= 1

    def render(self):
        self.renderer.clear()
        self.renderer.draw_target_zone()
        self.renderer.draw_lanes(self.lane_flash, self._pressed_lanes)
        self.renderer.draw_tiles(self.tiles)
        self.renderer.draw_input_status(
            self.input_active, self.input_label, self.input_activity,
            self.last_note, self.note_timer, self.msg_count,
        )
        self.renderer.draw_ui(
            self.score, self.combo, self.max_combo, self.speed,
            self.total_notes, self.hit_count, self.miss_count,
            self.rating_text,
        )
        pygame.display.flip()

    def _draw_results(self):
        self.renderer.clear()
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.renderer.screen.blit(s, (0, 0))
        self.renderer.draw_results(
            self.score, self.combo, self.max_combo,
            self.total_notes, self.hit_count, self.miss_count,
        )

    def _process_notes(self):
        while not self.note_queue.empty():
            kind, data, _ = self.note_queue.get_nowait()
            self.input_activity = 15
            self.msg_count += 1
            if kind != "note":
                continue
            note = data
            self.last_note = note
            self.note_timer = 30
            lane = (note - 40) % 6
            self._try_hit_lane(lane)

    def _try_hit_lane(self, lane: int):
        best = None
        best_delta = float("inf")
        for tile in self.tiles:
            if not tile.active or tile.lane != lane:
                continue
            delta = abs(tile.spawn_time - self.game_time)
            if delta < HIT_WINDOW_MISS and delta < best_delta:
                best = tile
                best_delta = delta
        if best is not None:
            self._register_hit(best, best_delta)

    def _register_hit(self, tile: Tile, delta: float):
        tile.hit = True
        tile.y = TARGET_Y
        self.hit_count += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        mult = 1 + (self.combo // COMBO_MULTIPLIER_STEP)
        mult = min(mult, MAX_COMBO_MULTIPLIER)
        if delta <= HIT_WINDOW_PERFECT:
            tile.hit_rating = "perfect"
            self.score += SCORE_PERFECT * mult
        elif delta <= HIT_WINDOW_GOOD:
            tile.hit_rating = "good"
            self.score += SCORE_GOOD * mult
        else:
            tile.hit_rating = "ok"
            self.score += SCORE_OK * mult
        if not self._is_audio:
            self.sound.play_note(tile.fret)
        self.rating_text = tile.hit_rating
        self.rating_timer = 30
        tile.flash_timer = 10
        self.lane_flash[tile.lane] = 8

        self._auto_slide(tile)

    def _auto_slide(self, hit_tile: Tile):
        for tile in self.tiles:
            if not tile.active:
                continue
            dt = abs(tile.spawn_time - hit_tile.spawn_time)
            if dt > SLIDE_THRESHOLD or dt < 0.5:
                continue
            dl = abs(tile.lane - hit_tile.lane)
            if dl > 2:
                continue
            tile.hit = True
            tile.y = TARGET_Y
            tile.hit_rating = "slide"
            self.hit_count += 1
            if not self._is_audio:
                self.sound.play_note(tile.fret)

    def _check_misses(self):
        for tile in self.tiles:
            if not tile.active:
                continue
            if self.game_time - tile.spawn_time > HIT_WINDOW_MISS:
                tile.missed = True
                self.combo = 0
                self.miss_count += 1

    def _check_finished(self):
        if self.miss_count + self.hit_count >= self.total_notes:
            self.finished_game = True
            self.show_results = True

    def cleanup(self):
        if hasattr(self, "_audio") and self._audio:
            self._audio.stop()
