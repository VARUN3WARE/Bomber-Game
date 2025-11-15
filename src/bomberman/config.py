"""Configuration constants for Bomberman"""
from typing import Final

CELL: Final[int] = 36                 # pixels per tile
MAP_W: Final[int] = 31                # width in tiles (odd nice)
MAP_H: Final[int] = 17                # height in tiles
WINDOW_W: Final[int] = MAP_W * CELL
WINDOW_H: Final[int] = MAP_H * CELL + 64  # HUD area

TICK_MS: Final[int] = 80              # game tick interval (ms)
BOMB_FUSE_MS: Final[int] = 2200       # bomb fuse in milliseconds
EXPLOSION_MS: Final[int] = 550        # explosion lifetime in ms
BOMB_POWER: Final[int] = 3
PLAYER_MAX_BOMBS: Final[int] = 1
BOT_MAX_BOMBS: Final[int] = 1
PLAYER_HEALTH: Final[int] = 3
BOT_HEALTH: Final[int] = 1
BOT_COUNT: Final[int] = 3
BOT_VISION: Final[int] = 7

# ===== TILE TYPES =====
EMPTY: Final[int] = 0
SOFT: Final[int] = 1
HARD: Final[int] = 2

# Power-ups
POWERUP_SPAWN_CHANCE: Final[float] = 0.16  # chance a destroyed soft wall spawns a pickup
POWERUP_TYPES: Final[tuple] = ("extra_bomb", "bomb_power", "health")

