import tkinter as tk
from typing import Any
from .config import WINDOW_W, WINDOW_H, CELL
from .utils import now_ms
from .config import POWERUP_TYPES
from .pathfinding import a_star_with_visited, dijkstra_with_visited, jps_simple_with_visited

class TkRenderer:
    def __init__(self, root:tk.Tk):
        self.root = root
        self.canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H, bg="#111")
        self.canvas.pack()

    def draw(self, game: Any):
        # game is expected to expose map, bots, players, bombs, explosions, msgs
        self.canvas.delete("all")
        # draw tiles
        for y in range(game.map.h):
            for x in range(game.map.w):
                left = x*CELL
                top = y*CELL
                tile = game.map.grid[y][x]
                if tile.in_explosion:
                    color = "#ffb26b"
                elif tile.ttype == 2:
                    color = "#444444"
                elif tile.ttype == 1:
                    color = "#a0522d"
                else:
                    color = "#202020"
                self.canvas.create_rectangle(left, top, left+CELL, top+CELL, fill=color, outline="#111")
                if tile.bomb is not None:
                    b = tile.bomb
                    rem = max(0, b.explode_at - now_ms())
                    scale = 0.45 + 0.5 * (rem / game.config.BOMB_FUSE_MS)
                    pad = int((1-scale) * CELL / 2)
                    self.canvas.create_oval(left+pad, top+pad, left+CELL-pad, top+CELL-pad, fill="#ffdd55", outline="#ccaa22")
        # draw explosions
        for exp in game.explosions:
            for (ex,ey) in exp.positions:
                left = ex*CELL; top = ey*CELL
                self.canvas.create_rectangle(left, top, left+CELL, top+CELL, fill="#ff8c42", outline="#f97306")
        # draw bots
        for b in game.bots:
            if not b.alive: continue
            left = b.x*CELL; top = b.y*CELL
            margin = 6
            self.canvas.create_rectangle(left+margin, top+margin, left+CELL-margin, top+CELL-margin, fill="#d54", outline="#900")
        # draw player
        p = game.players[0]
        left = p.x*CELL; top = p.y*CELL
        margin = 6
        color = "#4f4" if p.alive else "#666"
        self.canvas.create_rectangle(left+margin, top+margin, left+CELL-margin, top+CELL-margin, fill=color, outline="#060")
        # HUD
        hud_y = game.map.h * CELL + 8
        hud_text = f"HP: {p.health}  Score: {p.score}  Bombs: {p.bombs_active}/{p.max_bombs}  Time: {int((now_ms()/1000))}s"
        self.canvas.create_text(8, hud_y, anchor="w", fill="#eee", font=("Consolas", 13), text=hud_text)
        # messages
        if game.msgs:
            for i, m in enumerate(reversed(game.msgs[-4:])):
                self.canvas.create_text(8, hud_y + 22 + i*16, anchor="w", fill="#ddd", font=("Consolas", 11), text=m)
        # transient power-up HUD icon (spawn or pickup feedback)
        lpi = getattr(game, 'last_powerup_icon', None)
        if lpi is not None:
            ptype, end_at = lpi
            if end_at > now_ms():
                # draw icon at right side of HUD
                ix = WINDOW_W - 48
                iy = hud_y
                if ptype == "extra_bomb":
                    icolor = "#6ee"
                elif ptype == "bomb_power":
                    icolor = "#eec"
                elif ptype == "health":
                    icolor = "#8f8"
                else:
                    icolor = "#fff"
                pad = 6
                self.canvas.create_oval(ix+pad, iy-pad, ix+32-pad, iy+24-pad, fill=icolor, outline="#222")
                # small label
                self.canvas.create_text(ix+16, iy+28, text=ptype.replace("_"," "), fill="#ddd", font=("Consolas", 9))
        # update tile explosion flags
        for y in range(game.map.h):
            for x in range(game.map.w):
                game.map.grid[y][x].in_explosion = False
        for exp in game.explosions:
            for (ex,ey) in exp.positions:
                if game.map.in_bounds(ex,ey):
                    game.map.grid[ey][ex].in_explosion = True

        # draw power-ups
        for pu in getattr(game, 'powerups', []):
            left = pu.x * CELL; top = pu.y * CELL
            # choose color by type
            if pu.type == "extra_bomb":
                color = "#6ee"
            elif pu.type == "bomb_power":
                color = "#eec"
            elif pu.type == "health":
                color = "#8f8"
            else:
                color = "#fff"
            pad = CELL // 4
            self.canvas.create_oval(left+pad, top+pad, left+CELL-pad, top+CELL-pad, fill=color, outline="#222")

        # optional pathfinding visualization overlay
        pv = getattr(game, 'pathviz', None)
        if pv:
            # pv is expected to be a dict mapping algorithm name -> result dict
            colors = {'a*':'#3366ff', 'dijkstra':'#33aa33', 'jps':'#ff6666'}
            # Tkinter does not support alpha hex (RGBA). Use lighter solid colors for visited overlay.
            alpha_colors = {'a*': '#dfeaff', 'dijkstra':'#eaffdf','jps':'#ffe7e7'}
            offx = 0
            for key, res in pv.items():
                visited = res.get('visited', set()) or set()
                # draw visited nodes faintly
                for (vx,vy) in visited:
                    left = vx*CELL; top = vy*CELL
                    self.canvas.create_rectangle(left, top, left+CELL, top+CELL, fill=alpha_colors.get(key,'#ffffff22'), outline='')
                # draw path as thicker line
                path = res.get('path') or []
                for (i, coord) in enumerate(path):
                    px,py = coord
                    left = px*CELL; top = py*CELL
                    self.canvas.create_rectangle(left+6, top+6, left+CELL-6, top+CELL-6, fill=colors.get(key,'#fff'), outline='')
            # draw metrics text on HUD area
            hud_y = game.map.h * CELL + 8
            tx = 160
            for key, res in pv.items():
                txt = f"{key}: nodes={res.get('nodes_explored',0)} time={int(res.get('time_ms',0))}ms"
                self.canvas.create_text(tx, hud_y, anchor='w', fill='#eee', font=("Consolas",11), text=txt)
                tx += 240
