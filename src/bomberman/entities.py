from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set

@dataclass
class Tile:
    ttype: int = 0
    bomb: Optional["Bomb"] = None
    in_explosion: bool = False

@dataclass
class Entity:
    x: int
    y: int

    def pos(self) -> Tuple[int,int]:
        return (self.x, self.y)

@dataclass
class Bomberman(Entity):
    id: int
    health: int
    max_bombs: int = 1
    bomb_power: int = 3
    bombs_active: int = 0
    alive: bool = True
    score: int = 0

    def can_place(self) -> bool:
        return self.alive and self.bombs_active < self.max_bombs

@dataclass
class Player(Bomberman):
    pass

@dataclass
class Computer(Bomberman):
    vision: int = 7
    state: str = "search"
    target: Optional[Tuple[int,int]] = None
    path: List[Tuple[int,int]] = field(default_factory=list)
    last_think: int = field(default=0)
    think_interval_ms: int = 400

@dataclass
class Bomb(Entity):
    owner: Bomberman
    explode_at: int
    power: int = 3
    exploded: bool = False

@dataclass
class Explosion:
    positions: Set[Tuple[int,int]]
    end_at: int


@dataclass
class PowerUp:
    x: int
    y: int
    type: str

