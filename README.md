# Bomber-Game (Console Bomberman)

A small console-based Bomberman-like game (human vs bot) implemented in C++.

## Overview

This repository contains a simple console Bomberman clone where a human player (A) plays against an AI bot (X). The codebase includes a modular implementation with `Board`, `Player`, `Bomb`, `Game` and a Bot AI using depth-limited alpha-beta search with a heuristic evaluation. There are also some older/alternate game state files present in the root (legacy variants).

## What is implemented (current features)

- Console UI:

  - Renders the board to the terminal each tick.
  - Symbols: `A` = human player, `X` = bot, `*` = bomb, `@` = explosion site, `+` destructible wall, `#` indestructible wall, `.` free cell.
  - Player input via keyboard:
    - `w`/`a`/`s`/`d` — move up/left/down/right
    - `b` — place bomb (human only)
    - `p` — pass (in some implementations)

- Game mechanics:

  - Grid-based board with free cells, destructible walls, and indestructible walls.
  - Bomb placement, countdown, explosion with range and chain reactions.
  - Destructible walls can be destroyed by explosions.
  - Explosion affects players and can kill them; players can be killed resulting in game over.
  - Explosion chain reactions handled: bombs in explosion tiles are triggered.
  - Players can move over bombs (movement is allowed even if a bomb is present in many code paths).

- Bot AI:

  - Implemented in `src/bot.cpp` using a depth-limited alpha-beta search.
  - There is an `evaluate_state` function that scores states from the bot's perspective.
  - Difficulty menu in the console selects search depth (Easy/Medium/Hard → depths 2/4/5).
  - Notable bot rules from current code:
    - Bot tries to "run and hide": prefers distance from player and walls between itself and player.
    - Bot avoids placing bombs in the current `src/bot.cpp` implementation — only human can place bombs (an explicit design choice in that version).

- Two parallel code versions exist:
  - Primary modular implementation located in `src/` and `include/` (classes: `Board`, `Game`, `Player`, `Bomb`, `Bot`). Use `src/main.cpp` which ties these together.
  - An alternative/legacy implementation exists at repository root (files like `main.cpp`, `game.cpp`, `game.h`) which use different names and data structures (e.g., `GameState`). These files appear to be an earlier or alternate version and may be out-of-sync.

## Project structure (important files)

- `Makefile` — builds the project (`g++ -std=c++17 -Iinclude -Wall -g`) and places object files in `build/`.
- `src/` — primary source files:
  - `main.cpp` — console entry, menu for bot difficulty, main loop, player input handling.
  - `game.cpp` — `Game` implementation: init, tick, apply moves, bombs, explosions, win detection.
  - `board.cpp` — `Board` class: grid representation and layout parsing.
  - `bomb.cpp` — `Bomb` struct implementation.
  - `bot.cpp` — Bot AI implementation (alphabeta, evaluation, legal moves).
  - `player.cpp` — `Player` struct implementation.
- `include/` — public headers for the modular implementation:
  - `board.h`, `bomb.h`, `bot.h`, `game.h`, `player.h`.
- Root-level legacy files (alternate implementation): `main.cpp`, `game.cpp`, `game.h` — these use different types (`GameState`, different enums). They appear to be a separate working variant.

## How to build

From the project root (this repository's root) run:

```bash
make
```

This will compile `.cpp` files in `src/` (via `SRCDIR = src`) and produce an executable named `bomberman`.

## How to run

After building, run:

```bash
./bomberman
```

Follow the console prompts to select bot difficulty and then use the controls described above.

Note: If you prefer to use the legacy root `main.cpp` variant, you will need to adjust the `Makefile` or compile that file explicitly.

## Notable code behaviors & heuristics

- Explosion rules:

  - Bombs have a timer of (usually) 3 ticks (see `BOMB_TIMER` in `include/bomb.h` / `src/bomb.cpp`). When timer reaches 0 the bomb explodes this tick.
  - Explosion covers center + `range` cells orthogonally until blocked by indestructible walls; destructible walls are destroyed and stop propagation.
  - Chain reactions: bombs in explosion tiles explode immediately.

- Bot evaluation highlights:

  - Maximizes distance from the player and number of walls between bot and player (in `src/bot.cpp`).
  - Penalizes being trapped by imminent bombs.
  - Gives bonuses when the player is threatened.
  - Search is implemented with alpha-beta pruning; after the bot simulates a move, it assumes the human chooses the move minimizing the bot's evaluation.

- Differences between versions:
  - The modular `Game` in `src/game.cpp` and the legacy `GameState` in root have overlapping responsibilities and differing APIs. Be careful when modifying to ensure you edit the intended version.
