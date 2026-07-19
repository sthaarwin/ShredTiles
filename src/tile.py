from __future__ import annotations
from dataclasses import dataclass

from src.config import SCROLL_SPEED, TARGET_Y, SCREEN_HEIGHT, TILE_HEIGHT


@dataclass
class Tile:
    lane: int
    fret: int
    spawn_time: float
    channel: int = 0
    y: float = -100.0
    hit: bool = False
    missed: bool = False
    hit_rating: str = ""
    flash_timer: int = 0

    def update_y(self, game_time_ms: float):
        time_delta = self.spawn_time - game_time_ms
        self.y = TARGET_Y - time_delta * SCROLL_SPEED

    def is_onscreen(self) -> bool:
        return -TILE_HEIGHT - 50 < self.y < SCREEN_HEIGHT + 50

    @property
    def active(self) -> bool:
        return not self.hit and not self.missed
