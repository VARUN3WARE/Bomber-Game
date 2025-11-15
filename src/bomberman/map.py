import random
from typing import Optional, List
from .entities import Tile

class GameMap:
    def __init__(self, w:int, h:int, seed:Optional[int]=None):
        self.w = w
        self.h = h
        self.grid: List[List[Tile]] = [[Tile() for _ in range(w)] for _ in range(h)]
        self._generate(seed)

    def _generate(self, seed:Optional[int]):
        rng = random.Random(seed)
        # border hard walls
        for x in range(self.w):
            self.grid[0][x].ttype = 2
            self.grid[self.h-1][x].ttype = 2
        for y in range(self.h):
            self.grid[y][0].ttype = 2
            self.grid[y][self.w-1].ttype = 2
        # checkered hard walls
        for y in range(2, self.h-2):
            for x in range(2, self.w-2):
                if x % 2 == 0 and y % 2 == 0:
                    self.grid[y][x].ttype = 2
        # soft walls random (leave starting area)
        for y in range(1, self.h-1):
            for x in range(1, self.w-1):
                if self.grid[y][x].ttype != 0:
                    continue
                if (x <= 2 and y <= 2) or (x >= self.w-3 and y >= self.h-3):
                    continue
                if rng.random() < 0.52:
                    self.grid[y][x].ttype = 1

    def in_bounds(self, x:int, y:int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def is_walkable(self, x:int, y:int) -> bool:
        if not self.in_bounds(x,y): return False
        tile = self.grid[y][x]
        if tile.ttype in (1, 2): return False
        if tile.bomb is not None:
            return False
        return True

    def set_bomb(self, x:int, y:int, bomb:Optional[object]):
        self.grid[y][x].bomb = bomb

    def destroy_soft(self, x:int, y:int) -> bool:
        if not self.in_bounds(x,y): return False
        if self.grid[y][x].ttype == 1:
            self.grid[y][x].ttype = 0
            return True
        return False
