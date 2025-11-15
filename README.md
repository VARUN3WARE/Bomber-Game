# Bomberman (Tkinter) — Refactored

This is a small, refactored Python implementation of a tile-based Bomberman-like game using Tkinter for rendering.

This repository started from a single-file `main.py` and has been reorganized into a small package under `src/bomberman` to improve structure, testability and extensibility.

## What is included (summary of work done so far)

- Project reorganized into a package layout: `src/bomberman/`.
- Split the monolithic `main.py` into modular components:
  - `src/bomberman/config.py` — project constants and configuration.
  - `src/bomberman/utils.py` — small helpers (timing, manhattan, neighbors).
  - `src/bomberman/entities.py` — dataclasses for `Tile`, `Entity`, `Bomberman`, `Player`, `Computer`, `Bomb`, `Explosion`, and `PowerUp`.
  - `src/bomberman/map.py` — `GameMap` (map generation and tile logic).
  - `src/bomberman/ai.py` — `a_star` pathfinding implementation.
  - `src/bomberman/game.py` — `Game` engine: state, tick loop, AI update, bombs/explosions, and power-up logic.
  - `src/bomberman/renderer_tk.py` — `TkRenderer` renders game state to a Tkinter `Canvas` (kept separate from game logic).
  - `src/bomberman/main.py` — package entrypoint that creates the window, renderer and game loop.
  - Top-level `main.py` (launcher) — tiny launcher that inserts `src` on `sys.path` and calls `bomberman.main:main()` so `python3 main.py` still works.

New gameplay features added:

- Power-ups: `extra_bomb`, `bomb_power`, and `health`.
  - When a soft wall is destroyed there is a configurable chance to spawn a power-up.
  - Players can pick up power-ups by moving onto their tile; effects are applied immediately.
- HUD feedback: a transient HUD icon is shown briefly when a power-up spawns or is collected.

## How to run

1. Create and activate a virtual environment in the project root (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. (Optional) Upgrade pip inside the venv:

```bash
python -m pip install --upgrade pip
```

3. Install requirements (this project uses only the Python standard library; `tkinter` is required):

```bash
# No pip packages are required by default; keep requirements.txt for future deps
pip install -r requirements.txt
```

4. If `tkinter` is missing on Linux, install the OS package (examples):

````bash
# Debian / Ubuntu:
sudo apt update
sudo apt install python3-tk

# Fedora:
# Bomberman (Tkinter) — Refactored

This is a small, refactored Python implementation of a tile-based Bomberman-like game using Tkinter for rendering.

This repository started from a single-file `main.py` and has been reorganized into a small package under `src/bomberman` to improve structure, testability and extensibility.

## What is included (summary of work done so far)

- Project reorganized into a package layout: `src/bomberman/`.
- Split the monolithic `main.py` into modular components:
  - `src/bomberman/config.py` — project constants and configuration.
  - `src/bomberman/utils.py` — small helpers (timing, manhattan, neighbors).
  - `src/bomberman/entities.py` — dataclasses for `Tile`, `Entity`, `Bomberman`, `Player`, `Computer`, `Bomb`, `Explosion`, and `PowerUp`.
  - `src/bomberman/map.py` — `GameMap` (map generation and tile logic).
  - `src/bomberman/ai.py` — original A* helper (kept for compatibility).
  - `src/bomberman/pathfinding.py` — new: A*, Dijkstra and a simplified JPS-like algorithm with visited-node tracking.
  - `src/bomberman/pathfinding_visualizer.py` — helper to run algorithms, measure time and nodes explored.
  - `src/bomberman/game.py` — `Game` engine: state, tick loop, AI update, bombs/explosions, and power-up logic.
  - `src/bomberman/renderer_tk.py` — `TkRenderer` renders game state to a Tkinter `Canvas` (kept separate from game logic). It also draws optional pathfinding overlays.
  - `src/bomberman/main.py` — package entrypoint that creates the window, renderer and game loop.
  - Top-level `main.py` (launcher) — tiny launcher that inserts `src` on `sys.path` and calls `bomberman.main:main()` so `python3 main.py` still works.

New gameplay and tooling features added:

- Power-ups: `extra_bomb`, `bomb_power`, and `health`.
  - When a soft wall is destroyed there is a configurable chance to spawn a power-up.
  - Players can pick up power-ups by moving onto their tile; effects are applied immediately.
- HUD feedback: a transient HUD icon is shown briefly when a power-up spawns or is collected.
- Pathfinding comparison & visualization:
  - Implemented A* (visited-tracking), Dijkstra, and a simplified JPS-like algorithm in `pathfinding.py`.
  - `pathfinding_visualizer.py` times runs and records nodes explored.
  - Press `c` in-game (while a bot is alive) to compare pathfinding from the player to the first alive bot. Results are shown on the HUD and as overlays (visited nodes + paths).

## How to run

1. Create and activate a virtual environment in the project root (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
````

2. (Optional) Upgrade pip inside the venv:

```bash
python -m pip install --upgrade pip
```

3. Install requirements (this project uses only the Python standard library; `tkinter` is required):

```bash
# No pip packages are required by default; keep requirements.txt for future deps
pip install -r requirements.txt
```

4. If `tkinter` is missing on Linux, install the OS package (examples):

```bash
# Debian / Ubuntu:
sudo apt update
sudo apt install python3-tk

# Fedora:
sudo dnf install python3-tkinter

# Arch:
sudo pacman -S tk
```

5. Run the game from the project root:

```bash
python3 main.py
```

Controls

- Arrow keys or WASD: move the player
- Space: place bomb
- Q or Escape: quit
- C: run pathfinding comparison (player -> first alive bot) and visualize results

## Pathfinding visualization

- Press `c` to run the three algorithms and visualize results.
- HUD will show metrics like nodes explored and time in ms for each algorithm.
- The renderer overlays visited nodes (faint fill) and the resulting path (solid tiles) with different colors per algorithm.

## Important files and responsibilities

- `src/bomberman/game.py` — core game simulation. Keep game logic here. Make it testable by avoiding direct GUI calls inside logic methods.
- `src/bomberman/renderer_tk.py` — draws game state; should not modify game state. Also draws optional pathfinding overlays.
- `src/bomberman/pathfinding.py` — multi-algorithm implementations (A\*, Dijkstra, simplified JPS).
- `src/bomberman/pathfinding_visualizer.py` — runner that measures time & nodes.
- `src/bomberman/entities.py` — data structures for entities and pickups.

## Phase 1 plan (Foundation & Core AI Algorithms)

We are following a short roadmap for Weeks 1–2. Current status: pathfinding algorithms and visualization implemented (1.1 done). Next items:

1.2 Danger Zone Calculation (next):

- Implement Flood Fill algorithm for explosion prediction.
- Calculate safe zones and danger ratings per tile.
- Predict chain reactions (bombs triggering bombs).
- Create a danger heatmap overlay in the renderer.

Files: `src/bomberman/danger_analysis.py`, integrate into `src/bomberman/game.py`.

Deliverables:

- Real-time danger zone visualization.
- Safety scoring system for tiles.
- Chain reaction prediction.

  1.3 Finite State Machine (FSM) for bots (later this phase):

- Design AI states: EXPLORING, FLEEING, ATTACKING, COLLECTING, CAMPING.
- Implement state transitions based on conditions (danger, distance to player/soft walls/power-ups).
- Create visual state indicator in renderer.

Files: `src/bomberman/ai_fsm.py`, update `src/bomberman/entities.py` and `src/bomberman/game.py`.

Deliverables:

- Working FSM with 5+ states.
- Clear transition rules.
- Debug visualization of current state.

## Configuration & tuning

- `src/bomberman/config.py` contains constants like map size, tick rate, bomb fuse, explosion duration, and power-up spawn chance (`POWERUP_SPAWN_CHANCE`). Tweak values here for balancing.
