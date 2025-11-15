#!/usr/bin/env python3
"""
Bomberman (Tkinter)
- Tile-based Bomberman using Tkinter Canvas (no OpenGL).
- Player: '@' (green square), Bots: red, Soft walls: brown, Hard walls: dark gray
- Bomb: yellow circle, Explosion: orange/yellow
- Controls: Arrow keys / WASD to move, Space to place bomb, Q/Esc to quit
- Bots use A* pathfinding and a simple state machine.
"""

import tkinter as tk
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set, Dict
import heapq
import random
import time
import math

# ===== CONFIG =====
CELL = 36                 # pixels per tile
MAP_W = 31                # width in tiles (odd nice)
MAP_H = 17                # height in tiles
WINDOW_W = MAP_W * CELL
WINDOW_H = MAP_H * CELL + 64  # HUD area

TICK_MS = 80              # game tick interval (ms) => ~12.5 FPS; you can reduce for smoother
BOMB_FUSE_MS = 2200       # bomb fuse in milliseconds
EXPLOSION_MS = 550        # explosion lifetime in ms
BOMB_POWER = 3
PLAYER_MAX_BOMBS = 1
BOT_MAX_BOMBS = 1
PLAYER_HEALTH = 3
BOT_HEALTH = 1
BOT_COUNT = 3
BOT_VISION = 7

# ===== TILE TYPES =====
EMPTY = 0
SOFT = 1
HARD = 2

# ===== UTILS =====
def now_ms() -> int:
    return int(time.time() * 1000)

def manhattan(a:Tuple[int,int], b:Tuple[int,int]) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def neighbors(pos:Tuple[int,int]):
    x,y = pos
    return [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]

# ===== DATACLASSES =====
@dataclass
class Tile:
    ttype: int = EMPTY
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
    bomb_power: int = BOMB_POWER
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
    vision: int = BOT_VISION
    state: str = "search"           # 'search', 'chase', 'evade'
    target: Optional[Tuple[int,int]] = None
    path: List[Tuple[int,int]] = field(default_factory=list)
    last_think: int = field(default=0)
    think_interval_ms: int = 400

@dataclass
class Bomb(Entity):
    owner: Bomberman
    explode_at: int
    power: int = BOMB_POWER
    exploded: bool = False

@dataclass
class Explosion:
    positions: Set[Tuple[int,int]]
    end_at: int

# ===== GAME MAP =====
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
            self.grid[0][x].ttype = HARD
            self.grid[self.h-1][x].ttype = HARD
        for y in range(self.h):
            self.grid[y][0].ttype = HARD
            self.grid[y][self.w-1].ttype = HARD
        # checkered hard walls
        for y in range(2, self.h-2):
            for x in range(2, self.w-2):
                if x % 2 == 0 and y % 2 == 0:
                    self.grid[y][x].ttype = HARD
        # soft walls random (leave starting area)
        for y in range(1, self.h-1):
            for x in range(1, self.w-1):
                if self.grid[y][x].ttype != EMPTY:
                    continue
                if (x <= 2 and y <= 2) or (x >= self.w-3 and y >= self.h-3):
                    continue
                if rng.random() < 0.52:
                    self.grid[y][x].ttype = SOFT

    def in_bounds(self, x:int, y:int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def is_walkable(self, x:int, y:int) -> bool:
        if not self.in_bounds(x,y): return False
        tile = self.grid[y][x]
        if tile.ttype in (SOFT, HARD): return False
        if tile.bomb is not None:
            return False  # bombs block traversal for everyone
        return True

    def set_bomb(self, x:int, y:int, bomb:Optional[Bomb]):
        self.grid[y][x].bomb = bomb

    def destroy_soft(self, x:int, y:int) -> bool:
        if not self.in_bounds(x,y): return False
        if self.grid[y][x].ttype == SOFT:
            self.grid[y][x].ttype = EMPTY
            return True
        return False

# ===== PATHFINDING =====
def a_star(game_map:GameMap, start:Tuple[int,int], goal:Tuple[int,int], forbidden:Set[Tuple[int,int]]=set()) -> Optional[List[Tuple[int,int]]]:
    if start == goal:
        return []
    openh = []
    heapq.heappush(openh, (manhattan(start,goal), 0, start))
    came: Dict[Tuple[int,int], Tuple[int,int]] = {}
    gscore = {start: 0}
    closed = set()
    while openh:
        f,g,current = heapq.heappop(openh)
        if current in closed:
            continue
        if current == goal:
            # reconstruct
            path = []
            cur = current
            while cur != start:
                path.append(cur)
                cur = came[cur]
            path.reverse()
            return path
        closed.add(current)
        x,y = current
        for nx,ny in neighbors(current):
            if not game_map.in_bounds(nx,ny): continue
            if (nx,ny) in forbidden: continue
            tile = game_map.grid[ny][nx]
            # blocked by walls or bombs
            if tile.ttype != EMPTY: continue
            if tile.bomb is not None: continue
            tentative = g + 1
            if (nx,ny) not in gscore or tentative < gscore[(nx,ny)]:
                gscore[(nx,ny)] = tentative
                came[(nx,ny)] = current
                heapq.heappush(openh, (tentative + manhattan((nx,ny), goal), tentative, (nx,ny)))
    return None

# ===== ENTITY MANAGER & GAME =====
class Game:
    def __init__(self, root:tk.Tk):
        self.root = root
        self.canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H, bg="#111")
        self.canvas.pack()
        self.map = GameMap(MAP_W, MAP_H, seed=0xBEEF)
        self.players: List[Player] = []
        self.bots: List[Computer] = []
        self.bombs: List[Bomb] = []
        self.explosions: List[Explosion] = []
        self.next_id = 1
        self.msgs: List[str] = []
        self.last_msg = ""
        self.setup_entities()
        self.key_state = set()
        self._bind_keys()
        self.running = True
        self.last_tick = now_ms()
        self.root.after(TICK_MS, self.tick)
        self.draw()  # initial draw

    def setup_entities(self):
        # Player at top-left safe spot
        p = Player(x=1, y=1, id=self._gen_id(), health=PLAYER_HEALTH, max_bombs=PLAYER_MAX_BOMBS, bomb_power=BOMB_POWER)
        self.players.append(p)
        # bots at random empty tiles
        rng = random.Random()
        tries = 0
        positions = []
        while len(positions) < BOT_COUNT and tries < 1000:
            tries += 1
            x = rng.randint(1, self.map.w-2)
            y = rng.randint(1, self.map.h-2)
            if (x,y) == (p.x,p.y): continue
            if self.map.grid[y][x].ttype != EMPTY: continue
            positions.append((x,y))
        for pos in positions:
            b = Computer(x=pos[0], y=pos[1], id=self._gen_id(), health=BOT_HEALTH, max_bombs=BOT_MAX_BOMBS, bomb_power=BOMB_POWER)
            self.bots.append(b)

    def _gen_id(self) -> int:
        nid = self.next_id
        self.next_id += 1
        return nid

    def _bind_keys(self):
        self.root.bind("<KeyPress>", self.on_keypress)
        self.root.bind("<KeyRelease>", self.on_keyrelease)

    def on_keypress(self, event):
        k = event.keysym.lower()
        self.key_state.add(k)
        # direct actions on press
        if k in ("space",):
            self.place_bomb(self.players[0])
        if k in ("q","escape"):
            self.quit()

    def on_keyrelease(self, event):
        k = event.keysym.lower()
        if k in self.key_state:
            self.key_state.remove(k)

    def quit(self):
        self.running = False
        self.root.quit()

    def add_msg(self, text:str):
        self.last_msg = text
        self.msgs.append(text)
        if len(self.msgs) > 5:
            self.msgs.pop(0)

    # ---- bombs ----
    def place_bomb(self, owner:Bomberman) -> bool:
        if not owner.can_place():
            return False
        x,y = owner.x, owner.y
        tile = self.map.grid[y][x]
        if tile.bomb is not None:
            return False
        explosion_time = now_ms() + BOMB_FUSE_MS
        bomb = Bomb(x=x, y=y, owner=owner, explode_at=explosion_time, power=owner.bomb_power)
        self.bombs.append(bomb)
        self.map.set_bomb(x,y,bomb)
        owner.bombs_active += 1
        self.add_msg(f"Bomb placed by {owner.id} at {x},{y}")
        return True

    def explode_bomb(self, bomb:Bomb):
        if bomb.exploded: return
        bomb.exploded = True
        # clear bomb mapping
        self.map.set_bomb(bomb.x, bomb.y, None)
        try:
            self.bombs.remove(bomb)
        except ValueError:
            pass
        bomb.owner.bombs_active = max(0, bomb.owner.bombs_active - 1)
        # compute blast positions
        positions: Set[Tuple[int,int]] = {(bomb.x, bomb.y)}
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            for step in range(1, bomb.power+1):
                nx = bomb.x + dx*step
                ny = bomb.y + dy*step
                if not self.map.in_bounds(nx,ny):
                    break
                tile = self.map.grid[ny][nx]
                if tile.ttype == HARD:
                    break
                positions.add((nx,ny))
                # chain reaction
                if tile.bomb and not tile.bomb.exploded:
                    self.explode_bomb(tile.bomb)
                if tile.ttype == SOFT:
                    break
        # apply destruction and damage
        destroyed = 0
        for (x,y) in list(positions):
            if self.map.destroy_soft(x,y):
                destroyed += 1
        if destroyed:
            self.add_msg(f"{destroyed} soft wall(s) destroyed")
        # damage player
        for p in self.players:
            if p.alive and (p.x,p.y) in positions:
                p.health -= 1
                self.add_msg(f"Player hit! HP {p.health}")
                if p.health <= 0:
                    p.alive = False
                    self.add_msg("Player died!")
        # damage bots
        for b in self.bots:
            if b.alive and (b.x,b.y) in positions:
                b.health -= 1
                if b.health <= 0:
                    b.alive = False
                    if isinstance(bomb.owner, Player):
                        bomb.owner.score += 100
                    self.add_msg(f"Bot {b.id} killed by bomb")
        # create explosion object for visuals
        exp = Explosion(positions=positions, end_at=now_ms() + EXPLOSION_MS)
        self.explosions.append(exp)

    # ---- prediction and AI helpers ----
    def predict_danger(self, threshold_ms: int = 2000) -> Set[Tuple[int,int]]:
        danger = set()
        now = now_ms()
        for b in self.bombs:
            if b.explode_at - now <= threshold_ms:
                danger.add((b.x,b.y))
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    for step in range(1, b.power+1):
                        nx = b.x + dx*step
                        ny = b.y + dy*step
                        if not self.map.in_bounds(nx,ny): break
                        if self.map.grid[ny][nx].ttype == HARD: break
                        danger.add((nx,ny))
                        if self.map.grid[ny][nx].ttype == SOFT:
                            break
        return danger

    def find_safe_tiles(self, bot:Computer, danger:Set[Tuple[int,int]]) -> List[Tuple[int,int]]:
        from collections import deque
        start = (bot.x, bot.y)
        q = deque([start])
        visited = {start}
        safe = []
        steps = 0
        while q and steps < 1000:
            steps += 1
            cur = q.popleft()
            if cur not in danger and self.map.is_walkable(cur[0], cur[1]):
                safe.append(cur)
            for nx,ny in neighbors(cur):
                if not self.map.in_bounds(nx,ny): continue
                if (nx,ny) in visited: continue
                if not self.map.is_walkable(nx,ny): continue
                visited.add((nx,ny))
                q.append((nx,ny))
        return safe

    def find_nearest_soft(self, bot:Computer) -> Optional[Tuple[int,int]]:
        best = None
        bestd = 10**9
        for y in range(self.map.h):
            for x in range(self.map.w):
                if self.map.grid[y][x].ttype == SOFT:
                    d = manhattan((bot.x,bot.y),(x,y))
                    if d < bestd:
                        bestd = d
                        best = (x,y)
        return best

    # ---- AI ----
    def update_ai(self):
        now = now_ms()
        player = self.players[0]
        danger = self.predict_danger()
        for bot in self.bots:
            if not bot.alive:
                continue
            # throttle thinking
            if now - bot.last_think < bot.think_interval_ms:
                # continue following path if any
                self.follow_path_step(bot)
                continue
            bot.last_think = now
            # decide state
            if (bot.x,bot.y) in danger:
                bot.state = "evade"
            else:
                if manhattan((bot.x,bot.y),(player.x,player.y)) <= bot.vision:
                    bot.state = "chase"
                    bot.target = (player.x, player.y)
                else:
                    bot.state = "search"
                    bot.target = None
            # behavior
            if bot.state == "evade":
                safe = self.find_safe_tiles(bot, danger)
                if safe:
                    dest = min(safe, key=lambda p: manhattan((bot.x,bot.y), p))
                    path = a_star(self.map, (bot.x,bot.y), dest)
                    if path:
                        bot.path = path
                        self.follow_path_step(bot)
                    else:
                        self.random_move(bot)
                else:
                    self.random_move(bot)
            elif bot.state == "chase":
                path = a_star(self.map, (bot.x,bot.y), (player.x,player.y))
                if path and len(path) > 0:
                    bot.path = path
                    # place bomb occasionally if close
                    if manhattan((bot.x,bot.y),(player.x,player.y)) <= 2 and bot.can_place():
                        if random.random() < 0.3:
                            self.place_bomb(bot)
                    self.follow_path_step(bot)
                else:
                    self.random_move(bot)
            else:  # search
                target = self.find_nearest_soft(bot)
                if target:
                    path = a_star(self.map, (bot.x,bot.y), target)
                    if path:
                        bot.path = path
                        # if adjacent to soft wall, maybe place bomb
                        if len(path) <= 1 and bot.can_place() and random.random() < 0.6:
                            self.place_bomb(bot)
                        self.follow_path_step(bot)
                        continue
                self.random_move(bot)

    def follow_path_step(self, bot:Computer):
        if not bot.path:
            return
        nx,ny = bot.path[0]
        if self.map.is_walkable(nx,ny):
            bot.x, bot.y = nx, ny
            bot.path.pop(0)
        else:
            bot.path = []

    def random_move(self, bot:Computer):
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]
        random.shuffle(dirs)
        for dx,dy in dirs:
            nx,ny = bot.x + dx, bot.y + dy
            if self.map.in_bounds(nx,ny) and self.map.is_walkable(nx,ny):
                bot.x, bot.y = nx, ny
                return

    # ---- main tick ----
    def tick(self):
        if not self.running:
            return
        # handle player continuous input
        self.handle_input()
        # update AI
        self.update_ai()
        # bombs explode when time reached
        now = now_ms()
        for b in list(self.bombs):
            if now >= b.explode_at and not b.exploded:
                self.explode_bomb(b)
        # remove expired explosions
        self.explosions = [e for e in self.explosions if e.end_at > now]
        self.draw()
        self.root.after(TICK_MS, self.tick)

    def handle_input(self):
        p = self.players[0]
        if not p.alive: return
        dx = dy = 0
        # movement precedence: up/down/left/right from keys pressed
        if any(k in self.key_state for k in ("up","w")):
            dy = -1
        elif any(k in self.key_state for k in ("down","s")):
            dy = 1
        elif any(k in self.key_state for k in ("left","a")):
            dx = -1
        elif any(k in self.key_state for k in ("right","d")):
            dx = 1
        if dx != 0 or dy != 0:
            nx,ny = p.x + dx, p.y + dy
            if self.map.in_bounds(nx,ny) and self.map.is_walkable(nx,ny):
                p.x, p.y = nx, ny

    # ---- draw ----
    def draw(self):
        self.canvas.delete("all")
        # draw tiles
        for y in range(self.map.h):
            for x in range(self.map.w):
                left = x*CELL
                top = y*CELL
                tile = self.map.grid[y][x]
                if tile.in_explosion:
                    color = "#ffb26b"
                elif tile.ttype == HARD:
                    color = "#444444"
                elif tile.ttype == SOFT:
                    color = "#a0522d"
                else:
                    color = "#202020"
                self.canvas.create_rectangle(left, top, left+CELL, top+CELL, fill=color, outline="#111")
                # bomb
                if tile.bomb is not None:
                    # animated pulse
                    b = tile.bomb
                    rem = max(0, b.explode_at - now_ms())
                    scale = 0.45 + 0.5 * (rem / BOMB_FUSE_MS)
                    pad = int((1-scale) * CELL / 2)
                    self.canvas.create_oval(left+pad, top+pad, left+CELL-pad, top+CELL-pad, fill="#ffdd55", outline="#ccaa22")
        # draw explosions (overwrites)
        for exp in self.explosions:
            for (ex,ey) in exp.positions:
                left = ex*CELL; top = ey*CELL
                self.canvas.create_rectangle(left, top, left+CELL, top+CELL, fill="#ff8c42", outline="#f97306")
        # draw bots
        for b in self.bots:
            if not b.alive: continue
            left = b.x*CELL; top = b.y*CELL
            margin = 6
            self.canvas.create_rectangle(left+margin, top+margin, left+CELL-margin, top+CELL-margin, fill="#d54", outline="#900")
        # draw player
        p = self.players[0]
        left = p.x*CELL; top = p.y*CELL
        margin = 6
        color = "#4f4" if p.alive else "#666"
        self.canvas.create_rectangle(left+margin, top+margin, left+CELL-margin, top+CELL-margin, fill=color, outline="#060")
        # HUD
        hud_y = self.map.h * CELL + 8
        hud_text = f"HP: {p.health}  Score: {p.score}  Bombs: {p.bombs_active}/{p.max_bombs}  Time: {int((now_ms()/1000))}s"
        self.canvas.create_text(8, hud_y, anchor="w", fill="#eee", font=("Consolas", 13), text=hud_text)
        # messages
        if self.msgs:
            for i, m in enumerate(reversed(self.msgs[-4:])):
                self.canvas.create_text(8, hud_y + 22 + i*16, anchor="w", fill="#ddd", font=("Consolas", 11), text=m)
        # debug: draw bombs list / explosions
        # update tile explosion flags
        # first clear
        for y in range(self.map.h):
            for x in range(self.map.w):
                self.map.grid[y][x].in_explosion = False
        for exp in self.explosions:
            for (ex,ey) in exp.positions:
                if self.map.in_bounds(ex,ey):
                    self.map.grid[ey][ex].in_explosion = True

# ===== RUN =====
def main():
    root = tk.Tk()
    root.title("Bomberman - Tkinter")
    game = Game(root)
    root.protocol("WM_DELETE_WINDOW", game.quit)
    root.mainloop()

if __name__ == "__main__":
    main()
