import os

import pygame
import pygame._freetype

from src.config import (
    BG_COLOR, LANE_DIVIDER_COLOR, TARGET_ZONE_COLOR, TARGET_LINE_COLOR,
    UI_TEXT_COLOR, ACCENT_COLOR, MISS_COLOR, PERFECT_COLOR, GOOD_COLOR, OK_COLOR,
    SCREEN_WIDTH, SCREEN_HEIGHT, NUM_LANES, LANE_WIDTH, TILE_HEIGHT, TARGET_Y,
    LANE_COLORS, LANE_HIT_COLORS,
)
from src.tile import Tile


FONT_PATH = os.path.join(os.path.dirname(pygame._freetype.__file__), "freesansbold.ttf")


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        pygame._freetype.init()
        self.font_small = pygame._freetype.Font(FONT_PATH, 16)
        self.font_med = pygame._freetype.Font(FONT_PATH, 22)
        self.font_large = pygame._freetype.Font(FONT_PATH, 36)
        self.font_huge = pygame._freetype.Font(FONT_PATH, 60)

    def _render_text(self, font, text, color, bold=False):
        font.strong = bold
        surf, rect = font.render(text, color)
        return surf

    def clear(self):
        self.screen.fill(BG_COLOR)

    def draw_lanes(self, lane_flash: list[int], lane_press: set[int]):
        for i in range(NUM_LANES):
            x = i * LANE_WIDTH
            if lane_flash[i] > 0:
                s = pygame.Surface((LANE_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((*LANE_HIT_COLORS[i][:3], min(255, lane_flash[i] * 30)))
                self.screen.blit(s, (x, 0))
            elif i in lane_press:
                pygame.draw.rect(self.screen, (*LANE_COLORS[i], 40), (x, TARGET_Y, LANE_WIDTH, 200))

            pygame.draw.line(self.screen, LANE_DIVIDER_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)

    def draw_target_zone(self):
        pygame.draw.rect(self.screen, TARGET_ZONE_COLOR, (0, TARGET_Y, SCREEN_WIDTH, 4))
        pygame.draw.rect(self.screen, TARGET_LINE_COLOR, (0, TARGET_Y + 4, SCREEN_WIDTH, 2))

    def draw_tiles(self, tiles: list[Tile]):
        for tile in tiles:
            if not tile.active:
                if tile.flash_timer > 0:
                    x = tile.lane * LANE_WIDTH
                    c = PERFECT_COLOR if tile.hit_rating == "perfect" else GOOD_COLOR if tile.hit_rating == "good" else OK_COLOR
                    alpha = int(min(200, tile.flash_timer * 20))
                    s = pygame.Surface((LANE_WIDTH - 6, TILE_HEIGHT), pygame.SRCALPHA)
                    s.fill((*c, alpha))
                    self.screen.blit(s, (x + 3, tile.y))
                    tile.flash_timer -= 1
                continue

            x = tile.lane * LANE_WIDTH
            rect = pygame.Rect(x + 3, tile.y, LANE_WIDTH - 6, TILE_HEIGHT)

            color = LANE_COLORS[tile.lane]
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            bright = tuple(min(255, c + 60) for c in color)
            pygame.draw.rect(self.screen, bright, rect.inflate(-4, -4), border_radius=3)

            fret_surf = self._render_text(self.font_small, str(tile.fret), (255, 255, 255))
            tx = x + LANE_WIDTH // 2 - fret_surf.get_width() // 2
            ty = tile.y + TILE_HEIGHT // 2 - fret_surf.get_height() // 2
            self.screen.blit(fret_surf, (tx, ty))

    def draw_input_status(self, connected: bool, label_base: str, activity: int, last_note: int, note_timer: int, msg_count: int):
        if not connected:
            label = "No input"
            color = (120, 60, 60)
        else:
            base = label_base
            if last_note >= 0 and note_timer > 0:
                base += f"  note={last_note}  msgs={msg_count}"
            label = base
            color = (60, 255, 60) if activity > 0 else (100, 160, 100)

        surf = self._render_text(self.font_small, label, color)
        self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT - 20))

    def draw_ui(self, score: int, combo: int, max_combo: int, speed: float, total: int, hit: int, missed: int, rating: str = ""):
        score_surf = self._render_text(self.font_med, f"{score}", UI_TEXT_COLOR)
        self.screen.blit(score_surf, (15, 15))

        if combo > 1:
            color = ACCENT_COLOR if combo < 10 else PERFECT_COLOR
            font = self.font_large if combo >= 10 else self.font_med
            combo_surf = self._render_text(font, f"{combo}x", color)
            self.screen.blit(combo_surf, (15, 45))

        speed_surf = self._render_text(self.font_small, f"{int(speed * 100)}%", UI_TEXT_COLOR)
        self.screen.blit(speed_surf, (SCREEN_WIDTH - speed_surf.get_width() - 15, 15))

        prog = f"{hit + missed}/{total}" if total > 0 else "0/0"
        prog_surf = self._render_text(self.font_small, prog, UI_TEXT_COLOR)
        self.screen.blit(prog_surf, (SCREEN_WIDTH - prog_surf.get_width() - 15, 35))

        if rating:
            color = PERFECT_COLOR if rating == "perfect" else GOOD_COLOR if rating == "good" else OK_COLOR if rating == "ok" else MISS_COLOR
            rating_surf = self._render_text(self.font_large, rating.upper(), color)
            rx = SCREEN_WIDTH // 2 - rating_surf.get_width() // 2
            self.screen.blit(rating_surf, (rx, SCREEN_HEIGHT // 2 - 60))

    def draw_results(self, score: int, combo: int, max_combo: int, total: int, hit: int, missed: int):
        self.clear()
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.screen.blit(s, (0, 0))

        title = self._render_text(self.font_huge, "FINISHED!", ACCENT_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        items = [
            ("Score", f"{score}"),
            ("Hit", f"{hit}/{total} ({100 * hit // max(total, 1)}%)"),
            ("Max Combo", f"{max_combo}x"),
            ("Missed", str(missed)),
        ]
        y = 250
        for label, value in items:
            self.screen.blit(self._render_text(self.font_med, label, UI_TEXT_COLOR), (SCREEN_WIDTH // 2 - 180, y))
            self.screen.blit(self._render_text(self.font_med, value, ACCENT_COLOR), (SCREEN_WIDTH // 2 + 20, y))
            y += 50

        instr = self._render_text(self.font_small, "Press any key to quit", UI_TEXT_COLOR)
        self.screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, SCREEN_HEIGHT - 80))
        pygame.display.flip()
