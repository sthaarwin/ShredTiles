from __future__ import annotations

import pygame

from src.config import NUM_LANES, LANE_WIDTH, TARGET_Y, SCREEN_WIDTH, SCREEN_HEIGHT

LANE_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]


class InputHandler:
    def __init__(self):
        self.pressed_lanes: set[int] = set()
        self.just_pressed_lanes: list[int] = []

    def poll(self):
        self.just_pressed_lanes.clear()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                for lane, key in enumerate(LANE_KEYS):
                    if event.key == key:
                        self.just_pressed_lanes.append(lane)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if TARGET_Y <= my <= SCREEN_HEIGHT:
                    lane = mx // LANE_WIDTH
                    if 0 <= lane < NUM_LANES:
                        self.just_pressed_lanes.append(lane)

        keys = pygame.key.get_pressed()
        self.pressed_lanes = {lane for lane, key in enumerate(LANE_KEYS) if keys[key]}

        return True

    def get_just_pressed(self) -> list[int]:
        return self.just_pressed_lanes
