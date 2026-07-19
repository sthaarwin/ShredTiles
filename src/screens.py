from __future__ import annotations

import math

import pygame

from src.config import (
    BG_COLOR, UI_TEXT_COLOR, ACCENT_COLOR, MISS_COLOR, PERFECT_COLOR, GOOD_COLOR, OK_COLOR,
    SCREEN_WIDTH, SCREEN_HEIGHT, NUM_LANES, LANE_WIDTH, LANE_COLORS,
    SCREEN_HEIGHT, HIT_WINDOW_MISS,
)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Standard guitar tuning: string number -> MIDI note
STANDARD_TUNING = {6: 40, 5: 45, 4: 50, 3: 55, 2: 59, 1: 64}
STRING_NAMES = {6: "E", 5: "A", 4: "D", 3: "G", 2: "B", 1: "e"}


def midi_to_name(note: int) -> str:
    return NOTE_NAMES[note % 12] + str(note // 12 - 1)


def _draw_button(screen, renderer, rect, text, color, hovered):
    c = tuple(min(255, x + 40) for x in color) if hovered else color
    pygame.draw.rect(screen, c, rect, border_radius=8)
    pygame.draw.rect(screen, tuple(min(255, x + 20) for x in c), rect, 2, border_radius=8)
    surf = renderer._render_text(renderer.font_med, text, UI_TEXT_COLOR, bold=True)
    screen.blit(surf, (rect.centerx - surf.get_width() // 2, rect.centery - surf.get_height() // 2))


def _draw_item_row(screen, renderer, y, label, value, color, selected=False):
    lbl = renderer._render_text(renderer.font_med, label, UI_TEXT_COLOR)
    val = renderer._render_text(renderer.font_med, value, color)
    if selected:
        hl = pygame.Surface((SCREEN_WIDTH - 40, 40), pygame.SRCALPHA)
        hl.fill((100, 200, 255, 30))
        screen.blit(hl, (20, y + 4))
    screen.blit(lbl, (30, y + 8))
    screen.blit(val, (SCREEN_WIDTH - 30 - val.get_width(), y + 8))


class MainMenu:
    def __init__(self, app):
        self.app = app
        self.buttons = []
        self._build_buttons()

    def _build_buttons(self):
        bw, bh = 280, 50
        cx = SCREEN_WIDTH // 2 - bw // 2
        items = [
            ("PLAY", (6, 214, 160), self._play),
            ("TUNER", (100, 200, 255), self._tuner),
            ("QUIT", (239, 71, 111), self._quit),
        ]
        self.buttons = []
        for i, (text, color, action) in enumerate(items):
            y = 300 + i * 70
            self.buttons.append({"rect": pygame.Rect(cx, y, bw, bh), "text": text, "color": color, "action": action, "hovered": False})

    def enter(self):
        pass

    def _play(self):
        return "track_select"

    def _tuner(self):
        return "tuner"

    def _quit(self):
        self.app.running = False
        return None

    def handle_event(self, event):
        for b in self.buttons:
            if event.type == pygame.MOUSEMOTION:
                b["hovered"] = b["rect"].collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if b["hovered"]:
                    return b["action"]()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.running = False
        return None

    def update(self, dt):
        pass

    def render(self):
        r = self.app.renderer
        r.clear()

        title = r._render_text(r.font_huge, "ShredTiles", ACCENT_COLOR)
        r.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        sub = r._render_text(r.font_small, "Guitar practice game", UI_TEXT_COLOR)
        r.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 190))

        for b in self.buttons:
            _draw_button(r.screen, r, b["rect"], b["text"], b["color"], b["hovered"])


class TrackSelectScreen:
    def __init__(self, app):
        self.app = app
        self.tiles = []
        self.options = []
        self.selection = None
        self.error = ""

    def enter(self):
        self.tiles = self.app.tiles
        self.options = []
        self.selection = 0
        self.error = ""
        # Options are from midi_loader data, stored on app
        if hasattr(self.app, "_track_options"):
            self.options = self.app._track_options

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "menu"
            if event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.options:
                opt = self.options[self.selection]
                self.app.selected_channel = opt.get("channel")
                self.app.selected_track_index = opt.get("track_index", 0)
                self.app._load_tiles()
                return "input_select"
            if event.key == pygame.K_UP:
                self.selection = max(0, self.selection - 1)
            if event.key == pygame.K_DOWN:
                self.selection = min(len(self.options) - 1, self.selection + 1)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, opt in enumerate(self.options):
                y = 200 + i * 40
                if pygame.Rect(20, y, SCREEN_WIDTH - 40, 40).collidepoint(event.pos):
                    self.selection = i
                    self.app.selected_channel = opt.get("channel")
                    self.app.selected_track_index = opt.get("track_index", 0)
                    self.app._load_tiles()
                    return "input_select"

            # Back button
            if pygame.Rect(20, SCREEN_HEIGHT - 60, 120, 36).collidepoint(event.pos):
                return "menu"

        return None

    def update(self, dt):
        pass

    def render(self):
        r = self.app.renderer
        r.clear()

        title = r._render_text(r.font_large, "SELECT TRACK", UI_TEXT_COLOR)
        r.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        for i, opt in enumerate(self.options):
            y = 200 + i * 44
            label = opt["label"]
            count = opt["count"]
            color = LANE_COLORS[i % NUM_LANES]
            _draw_item_row(r.screen, r, y, f"[{opt['key']}]", f"{label}  ({count})", color, i == self.selection)

        if self.error:
            err = r._render_text(r.font_small, self.error, MISS_COLOR)
            r.screen.blit(err, (SCREEN_WIDTH // 2 - err.get_width() // 2, SCREEN_HEIGHT - 100))

        _draw_button(r.screen, r, pygame.Rect(20, SCREEN_HEIGHT - 60, 120, 36), "BACK", (80, 80, 100), False)

        n = len(self.options)
        if n > 0:
            hint = r._render_text(r.font_small, "Click or use arrows + Enter", UI_TEXT_COLOR)
            r.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 100))


class InputSelectScreen:
    def __init__(self, app):
        self.app = app
        self.options = []
        self.selection = 0
        self.midi_ports = []
        self.audio_devices = []

    def enter(self):
        self.options = []
        self.selection = 0
        from src.audio_input import list_audio_devices
        import mido

        self.midi_ports = []
        self.audio_devices = []
        try:
            self.midi_ports = list(enumerate(mido.get_input_names()))
        except Exception:
            pass
        self.audio_devices = list_audio_devices()

        self.options = []
        for i, (_, name) in enumerate(self.midi_ports):
            self.options.append({"type": "midi", "device": i, "name": name, "label": f"MIDI: {name}", "key": i})
        for dev_id, name in self.audio_devices:
            self.options.append({"type": "audio", "device": dev_id, "name": name, "label": f"Audio: {name}", "key": f"a{dev_id}"})
        self.options.append({"type": "none", "device": None, "name": "Keyboard/Mouse", "label": "Keyboard / Mouse only", "key": "k"})

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "track_select"
            if event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.options:
                return self._confirm()
            if event.key == pygame.K_UP:
                self.selection = max(0, self.selection - 1)
            if event.key == pygame.K_DOWN:
                self.selection = min(len(self.options) - 1, self.selection + 1)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, opt in enumerate(self.options):
                y = 200 + i * 44
                if pygame.Rect(20, y, SCREEN_WIDTH - 40, 40).collidepoint(event.pos):
                    self.selection = i
                    return self._confirm()

            if pygame.Rect(20, SCREEN_HEIGHT - 60, 120, 36).collidepoint(event.pos):
                return "track_select"

        return None

    def _confirm(self):
        opt = self.options[self.selection]
        self.app.input_cfg = opt
        return "gameplay"

    def update(self, dt):
        pass

    def render(self):
        r = self.app.renderer
        r.clear()

        title = r._render_text(r.font_large, "SELECT INPUT", UI_TEXT_COLOR)
        r.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        for i, opt in enumerate(self.options):
            y = 200 + i * 44
            t = opt["type"]
            label = opt["label"]
            if t == "midi":
                color = (100, 200, 255)
            elif t == "audio":
                color = (255, 200, 100)
            else:
                color = (160, 160, 160)
            _draw_item_row(r.screen, r, y, label, "", color, i == self.selection)

        _draw_button(r.screen, r, pygame.Rect(20, SCREEN_HEIGHT - 60, 120, 36), "BACK", (80, 80, 100), False)

        hint = r._render_text(r.font_small, "Click or use arrows + Enter", UI_TEXT_COLOR)
        r.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 100))


class TunerScreen:
    def __init__(self, app):
        self.app = app
        self.detected_note = -1
        self.detected_freq = 0.0
        self.rms = 0.0
        self.audio = None
        self._queue = None
        self._error = ""

    def enter(self):
        from src.audio_input import AudioPitchDetector, list_audio_devices

        self.detected_note = -1
        self.detected_freq = 0.0
        self.rms = 0.0
        self._cents = 0.0
        self._error = ""

        devices = list_audio_devices()
        if not devices:
            self._error = "No audio input devices found"
            return

        self.audio = AudioPitchDetector()
        self._queue = self.audio.queue

        try:
            import sounddevice as sd
            dev = sd.default.device[0]
        except Exception:
            dev = devices[0][0]

        try:
            self.audio.start(device=dev)
        except Exception as e:
            self._error = f"Audio error: {e}"
            self.audio = None
            self._queue = None

    def _leave(self):
        if self.audio:
            self.audio.stop()
            self.audio = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self._leave()
                return "menu"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(SCREEN_WIDTH - 140, 20, 120, 36).collidepoint(event.pos):
                self._leave()
                return "menu"
        return None

    def update(self, dt):
        if self._queue is None:
            return
        try:
            while not self._queue.empty():
                kind, data, cents = self._queue.get_nowait()
                if kind == "note":
                    self.detected_note = data
                    self._cents = cents
                    self.detected_freq = 440.0 * (2.0 ** ((data - 69) / 12.0))
        except Exception:
            pass
        if self.detected_note < 0:
            self.detected_freq = 0.0

    def _nearest_string(self, note: int):
        best = None
        best_dist = 999
        for s, n in STANDARD_TUNING.items():
            dist = abs(note - n)
            if dist < best_dist:
                best_dist = dist
                best = (s, n)
        return best

    def render(self):
        r = self.app.renderer
        r.clear()

        _draw_button(r.screen, r, pygame.Rect(SCREEN_WIDTH - 140, 20, 120, 36), "BACK", (80, 80, 100), False)

        title = r._render_text(r.font_large, "GUITAR TUNER", ACCENT_COLOR)
        r.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        # Draw string indicators
        string_y = 160
        for s in range(6, 0, -1):
            xn = (6 - s) * (SCREEN_WIDTH // 6)
            xw = SCREEN_WIDTH // 6
            target = STANDARD_TUNING[s]
            rect = pygame.Rect(xn, string_y, xw, 60)

            match = self.detected_note >= 0 and self._nearest_string(self.detected_note)[0] == s
            color = LANE_COLORS[6 - s] if match else (40, 40, 60)
            if match:
                pygame.draw.rect(r.screen, color, rect, border_radius=6)
                pygame.draw.rect(r.screen, tuple(min(255, c + 60) for c in color), rect, 2, border_radius=6)
            else:
                pygame.draw.rect(r.screen, color, rect, border_radius=6)
                pygame.draw.rect(r.screen, (60, 60, 80), rect, 2, border_radius=6)

            name = r._render_text(r.font_huge, STRING_NAMES[s], (255, 255, 255) if match else (120, 120, 140))
            r.screen.blit(name, (xn + xw // 2 - name.get_width() // 2, string_y + 8))

            tn = r._render_text(r.font_small, midi_to_name(target), (150, 150, 160))
            r.screen.blit(tn, (xn + xw // 2 - tn.get_width() // 2, string_y + 36))

        # Detected note display
        if self.detected_note >= 0:
            ny = 320
            note_name = midi_to_name(self.detected_note)
            note_surf = r._render_text(r.font_huge, note_name, ACCENT_COLOR)
            r.screen.blit(note_surf, (SCREEN_WIDTH // 2 - note_surf.get_width() // 2, ny))

            freq_surf = r._render_text(r.font_small, f"{self.detected_freq:.1f} Hz", UI_TEXT_COLOR)
            r.screen.blit(freq_surf, (SCREEN_WIDTH // 2 - freq_surf.get_width() // 2, ny + 70))

            # Nearest string + cents
            s, target_note = self._nearest_string(self.detected_note)
            cents = 1200 * math.log2(self.detected_freq / (440.0 * (2.0 ** ((target_note - 69) / 12.0))))
            if hasattr(self, "_cents") and self._cents is not None:
                cents = self._cents

            str_surf = r._render_text(r.font_med, f"String {s} ({STRING_NAMES[s]})", UI_TEXT_COLOR)
            r.screen.blit(str_surf, (SCREEN_WIDTH // 2 - str_surf.get_width() // 2, ny + 100))

            # Cents meter
            meter_y = ny + 140
            meter_w = 300
            meter_h = 20
            cx = SCREEN_WIDTH // 2
            pygame.draw.rect(r.screen, (40, 40, 60), (cx - meter_w // 2, meter_y, meter_w, meter_h), border_radius=4)
            pygame.draw.line(r.screen, (80, 80, 100), (cx, meter_y), (cx, meter_y + meter_h), 2)

            if abs(cents) < 50:
                bar_w = int((50 - abs(cents)) / 50 * (meter_w // 2))
                bar_color = GOOD_COLOR if abs(cents) < 15 else OK_COLOR
                if cents < 0:
                    bar_x = cx - bar_w
                else:
                    bar_x = cx
                pygame.draw.rect(r.screen, bar_color, (bar_x, meter_y + 2, bar_w, meter_h - 4), border_radius=3)

            cents_str = r._render_text(r.font_small, f"{cents:+.1f} cents", UI_TEXT_COLOR)
            r.screen.blit(cents_str, (SCREEN_WIDTH // 2 - cents_str.get_width() // 2, meter_y + meter_h + 10))

            # Tuning status
            if abs(cents) < 15:
                status = "IN TUNE"
                sc = GOOD_COLOR
            elif abs(cents) < 50:
                status = "SLIGHTLY OFF"
                sc = OK_COLOR
            else:
                status = "OUT OF TUNE"
                sc = MISS_COLOR
            st = r._render_text(r.font_large, status, sc)
            r.screen.blit(st, (SCREEN_WIDTH // 2 - st.get_width() // 2, meter_y + 50))

        elif self._error:
            err = r._render_text(r.font_small, self._error, MISS_COLOR)
            r.screen.blit(err, (SCREEN_WIDTH // 2 - err.get_width() // 2, 340))
        else:
            waiting = r._render_text(r.font_large, "PLAY A NOTE", (80, 80, 100))
            r.screen.blit(waiting, (SCREEN_WIDTH // 2 - waiting.get_width() // 2, 340))


class GameplayScreen:
    def __init__(self, app):
        self.app = app
        self._game = None
        self._countdown = 0
        self._countdown_timer = 0.0
        self._paused = False

    def enter(self):
        from src.game import Game
        self.app._load_tiles()
        self.app._init_audio_engine()
        self._game = Game(
            self.app.tiles,
            self.app.input_cfg,
            renderer=self.app.renderer,
            screen=self.app.screen,
            clock=self.app.clock,
            sound=self.app.sound if hasattr(self.app, 'sound') else None,
        )
        self._countdown = 3
        self._countdown_timer = 1000.0
        self._paused = False

    def _leave(self):
        if self._game:
            self._game.cleanup()
            self._game = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._countdown == 0:
                    self._paused = not self._paused
                return None
            if event.key == pygame.K_r and self._paused:
                self._leave()
                self.enter()
                return None
            if event.key in (pygame.K_b, pygame.K_m) and self._paused:
                self._leave()
                return "menu"
        if self._game and self._countdown == 0 and not self._paused:
            self._game.handle_event(event)
        return None

    def update(self, dt):
        if not self._game:
            return

        if self._countdown > 0:
            self._countdown_timer -= dt
            if self._countdown_timer <= 0:
                self._countdown -= 1
                self._countdown_timer = 1000.0
                if self._countdown == 0:
                    self._game.game_started = True
            return

        if self._paused:
            return

        self._game.update(dt)
        if self._game.show_results:
            self.app._last_game_state = {
                "score": self._game.score,
                "hit": self._game.hit_count,
                "total": self._game.total_notes,
                "max_combo": self._game.max_combo,
                "missed": self._game.miss_count,
            }
            return "results"

    def render(self):
        if not self._game:
            return

        r = self.app.renderer
        r.clear()
        r.draw_target_zone()
        r.draw_lanes(self._game.lane_flash, self._game._pressed_lanes)
        r.draw_tiles(self._game.tiles)
        r.draw_input_status(
            self._game.input_active, self._game.input_label, self._game.input_activity,
            self._game.last_note, self._game.note_timer, self._game.msg_count,
        )
        r.draw_ui(
            self._game.score, self._game.combo, self._game.max_combo, self._game.speed,
            self._game.total_notes, self._game.hit_count, self._game.miss_count,
        )

        if self._countdown > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            r.screen.blit(overlay, (0, 0))

            text = str(self._countdown)
            color = ACCENT_COLOR
            size = self._countdown_timer / 1000.0
            scale = 1.0 + (1.0 - size) * 0.3
            # Simulate scaling by picking font size
            font = r.font_huge
            surf = r._render_text(font, text, color, bold=True)
            rx = SCREEN_WIDTH // 2 - surf.get_width() // 2
            ry = SCREEN_HEIGHT // 2 - surf.get_height() // 2
            r.screen.blit(surf, (rx, ry))

        if self._paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            r.screen.blit(overlay, (0, 0))

            pause_text = r._render_text(r.font_huge, "PAUSED", ACCENT_COLOR)
            r.screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - 80))

            hint = r._render_text(r.font_small, "ESC to resume   R to restart   B to home", UI_TEXT_COLOR)
            r.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

        pygame.display.flip()


class ResultsScreen:
    def __init__(self, app):
        self.app = app

    def enter(self):
        pass

    def handle_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            return "menu"
        return None

    def update(self, dt):
        pass

    def render(self):
        g = getattr(self.app, "_last_game_state", None)
        r = self.app.renderer
        r.clear()
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        r.screen.blit(s, (0, 0))

        if g:
            title = r._render_text(r.font_huge, "FINISHED!", ACCENT_COLOR)
            r.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))
            items = [
                ("Score", str(g["score"])),
                ("Hit", f"{g['hit']}/{g['total']} ({100 * g['hit'] // max(g['total'], 1)}%)"),
                ("Max Combo", f"{g['max_combo']}x"),
                ("Missed", str(g["missed"])),
            ]
            y = 250
            for label, value in items:
                r.screen.blit(r._render_text(r.font_med, label, UI_TEXT_COLOR), (SCREEN_WIDTH // 2 - 180, y))
                r.screen.blit(r._render_text(r.font_med, value, ACCENT_COLOR), (SCREEN_WIDTH // 2 + 20, y))
                y += 50

        instr = r._render_text(r.font_small, "Click or press any key", UI_TEXT_COLOR)
        r.screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, SCREEN_HEIGHT - 80))
