import random
from typing import List, Optional, Tuple, Set
from .entities import Player, Computer, Bomb, Explosion, PowerUp
from .map import GameMap
from .utils import now_ms, neighbors, manhattan
from . import config
from .ai import a_star

class Game:
    def __init__(self, root, renderer):
        self.root = root
        self.renderer = renderer
        self.config = config
        self.map = GameMap(config.MAP_W, config.MAP_H, seed=0xBEEF)
        self.players: List[Player] = []
        self.bots: List[Computer] = []
        self.bombs: List[Bomb] = []
        self.explosions: List[Explosion] = []
        self.powerups: List[PowerUp] = []
        self.last_powerup_icon = None  # (type, end_at_ms)
        self.next_id = 1
        self.msgs: List[str] = []
        self.last_msg = ""
        self.setup_entities()
        self.key_state = set()
        self._bind_keys()
        self.running = True
        self.last_tick = now_ms()
        self.root.after(config.TICK_MS, self.tick)
        self.renderer.draw(self)

    def setup_entities(self):
        p = Player(x=1, y=1, id=self._gen_id(), health=config.PLAYER_HEALTH, max_bombs=config.PLAYER_MAX_BOMBS, bomb_power=config.BOMB_POWER)
        self.players.append(p)
        rng = random.Random()
        tries = 0
        positions = []
        while len(positions) < config.BOT_COUNT and tries < 1000:
            tries += 1
            x = rng.randint(1, self.map.w-2)
            y = rng.randint(1, self.map.h-2)
            if (x,y) == (p.x,p.y): continue
            if self.map.grid[y][x].ttype != 0: continue
            positions.append((x,y))
        for pos in positions:
            b = Computer(x=pos[0], y=pos[1], id=self._gen_id(), health=config.BOT_HEALTH, max_bombs=config.BOT_MAX_BOMBS, bomb_power=config.BOMB_POWER)
            self.bots.append(b)

    def _gen_id(self) -> int:
        nid = self.next_id
        self.next_id += 1
        return nid

    def _bind_keys(self):
        self.root.bind("<KeyPress>", self.on_keypress)
        self.root.bind("<KeyRelease>", self.on_keyrelease)
        # debug / visualization keys
        self.root.bind("<KeyPress-c>", self.on_compare_paths)

    def on_keypress(self, event):
        k = event.keysym.lower()
        self.key_state.add(k)
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

    def on_compare_paths(self, event=None):
        """Run a pathfinding comparison between A*, Dijkstra and JPS from the player to the first alive bot."""
        # toggle off if already showing
        if getattr(self, 'pathviz', None):
            self.pathviz = None
            self.add_msg("Pathviz cleared")
            return
        # find a living bot and the player
        if not self.bots:
            self.add_msg("No bots to compare to")
            return
        player = self.players[0]
        bot = None
        for b in self.bots:
            if b.alive:
                bot = b
                break
        if bot is None:
            self.add_msg("No alive bots to compare to")
            return
        start = (player.x, player.y)
        goal = (bot.x, bot.y)
        # run the three algorithms and store results for renderer with safety
        try:
            from .pathfinding_visualizer import run_and_record
            from .pathfinding import a_star_with_visited, dijkstra_with_visited, jps_simple_with_visited
            pv = {}
            pv['a*'] = run_and_record(a_star_with_visited, self.map, start, goal)
            pv['dijkstra'] = run_and_record(dijkstra_with_visited, self.map, start, goal)
            pv['jps'] = run_and_record(jps_simple_with_visited, self.map, start, goal)
            self.pathviz = pv
            # log a short summary
            for k,res in pv.items():
                self.add_msg(f"{k}: nodes={res.get('nodes_explored',0)} time={int(res.get('time_ms',0))}ms")
        except Exception as e:
            # write traceback to a log for inspection
            try:
                import traceback, datetime
                ts = datetime.datetime.now().isoformat()
                with open('pathviz_error.log', 'a') as fh:
                    fh.write(f"[{ts}] Pathviz error: {e}\n")
                    traceback.print_exc(file=fh)
            except Exception:
                pass
            self.add_msg(f"Pathviz failed: {e}")

    def add_msg(self, text:str):
        self.last_msg = text
        self.msgs.append(text)
        if len(self.msgs) > 5:
            self.msgs.pop(0)

    def place_bomb(self, owner:Bomb) -> bool:
        if not owner.can_place():
            return False
        x,y = owner.x, owner.y
        tile = self.map.grid[y][x]
        if tile.bomb is not None:
            return False
        explosion_time = now_ms() + config.BOMB_FUSE_MS
        bomb = Bomb(x=x, y=y, owner=owner, explode_at=explosion_time, power=owner.bomb_power)
        self.bombs.append(bomb)
        self.map.set_bomb(x,y,bomb)
        owner.bombs_active += 1
        self.add_msg(f"Bomb placed by {owner.id} at {x},{y}")
        return True

    def explode_bomb(self, bomb:Bomb):
        if bomb.exploded: return
        bomb.exploded = True
        self.map.set_bomb(bomb.x, bomb.y, None)
        try:
            self.bombs.remove(bomb)
        except ValueError:
            pass
        bomb.owner.bombs_active = max(0, bomb.owner.bombs_active - 1)
        positions: Set[Tuple[int,int]] = {(bomb.x, bomb.y)}
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            for step in range(1, bomb.power+1):
                nx = bomb.x + dx*step
                ny = bomb.y + dy*step
                if not self.map.in_bounds(nx,ny):
                    break
                tile = self.map.grid[ny][nx]
                if tile.ttype == 2:
                    break
                positions.add((nx,ny))
                if tile.bomb and not tile.bomb.exploded:
                    self.explode_bomb(tile.bomb)
                if tile.ttype == 1:
                    break
        destroyed = 0
        destroyed_positions = []
        for (x,y) in list(positions):
            if self.map.destroy_soft(x,y):
                destroyed += 1
                destroyed_positions.append((x,y))
        if destroyed:
            self.add_msg(f"{destroyed} soft wall(s) destroyed")
            # spawn power-ups on some destroyed tiles
            for (dx,dy) in destroyed_positions:
                import random as _rand
                if _rand.random() < self.config.POWERUP_SPAWN_CHANCE:
                    ptype = _rand.choice(self.config.POWERUP_TYPES)
                    pu = PowerUp(x=dx, y=dy, type=ptype)
                    self.powerups.append(pu)
                    # show transient HUD icon
                    self.last_powerup_icon = (ptype, now_ms() + 1800)
                    self.add_msg(f"Power-up '{ptype}' spawned at {dx},{dy}")
        for p in self.players:
            if p.alive and (p.x,p.y) in positions:
                p.health -= 1
                self.add_msg(f"Player hit! HP {p.health}")
                if p.health <= 0:
                    p.alive = False
                    self.add_msg("Player died!")
        for b in self.bots:
            if b.alive and (b.x,b.y) in positions:
                b.health -= 1
                if b.health <= 0:
                    b.alive = False
                    if hasattr(bomb.owner, 'score'):
                        if isinstance(bomb.owner, Player):
                            bomb.owner.score += 100
                    self.add_msg(f"Bot {b.id} killed by bomb")
        exp = Explosion(positions=positions, end_at=now_ms() + config.EXPLOSION_MS)
        self.explosions.append(exp)

    def apply_powerup(self, player: Player, pu: PowerUp):
        # apply immediate effects
        if pu.type == "extra_bomb":
            player.max_bombs += 1
            self.add_msg("Picked up Extra Bomb!")
        elif pu.type == "bomb_power":
            player.bomb_power += 1
            self.add_msg("Picked up Bomb Power!")
        elif pu.type == "health":
            player.health = min(self.config.PLAYER_HEALTH, player.health + 1)
            self.add_msg("Picked up Health!")
        # transient HUD icon for collection
        self.last_powerup_icon = (pu.type, now_ms() + 1800)

    def collect_powerups_at(self, x:int, y:int):
        # return any powerups at (x,y) and remove them
        taken = [pu for pu in self.powerups if pu.x == x and pu.y == y]
        if not taken:
            return []
        for pu in taken:
            try:
                self.powerups.remove(pu)
            except ValueError:
                pass
        return taken

    # AI helpers
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
                        if self.map.grid[ny][nx].ttype == 2: break
                        danger.add((nx,ny))
                        if self.map.grid[ny][nx].ttype == 1:
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

    def find_nearest_soft(self, bot:Computer):
        best = None
        bestd = 10**9
        for y in range(self.map.h):
            for x in range(self.map.w):
                if self.map.grid[y][x].ttype == 1:
                    d = manhattan((bot.x,bot.y),(x,y))
                    if d < bestd:
                        bestd = d
                        best = (x,y)
        return best

    def update_ai(self):
        now = now_ms()
        player = self.players[0]
        danger = self.predict_danger()
        for bot in self.bots:
            if not bot.alive:
                continue
            if now - bot.last_think < bot.think_interval_ms:
                self.follow_path_step(bot)
                continue
            bot.last_think = now
            if (bot.x,bot.y) in danger:
                bot.state = "evade"
            else:
                if manhattan((bot.x,bot.y),(player.x,player.y)) <= bot.vision:
                    bot.state = "chase"
                    bot.target = (player.x, player.y)
                else:
                    bot.state = "search"
                    bot.target = None
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
                    if manhattan((bot.x,bot.y),(player.x,player.y)) <= 2 and bot.can_place():
                        if random.random() < 0.3:
                            self.place_bomb(bot)
                    self.follow_path_step(bot)
                else:
                    self.random_move(bot)
            else:
                target = self.find_nearest_soft(bot)
                if target:
                    path = a_star(self.map, (bot.x,bot.y), target)
                    if path:
                        bot.path = path
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

    def tick(self):
        if not self.running:
            return
        self.handle_input()
        self.update_ai()
        now = now_ms()
        for b in list(self.bombs):
            if now >= b.explode_at and not b.exploded:
                self.explode_bomb(b)
        self.explosions = [e for e in self.explosions if e.end_at > now]
        self.renderer.draw(self)
        self.root.after(config.TICK_MS, self.tick)

    def handle_input(self):
        p = self.players[0]
        if not p.alive: return
        dx = dy = 0
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
                # check pickups
                taken = self.collect_powerups_at(p.x, p.y)
                for pu in taken:
                    self.apply_powerup(p, pu)
