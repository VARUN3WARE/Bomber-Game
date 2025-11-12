// game.h
#pragma once
#include <vector>
#include <string>
#include <optional>

enum Cell : int {
    FREE = 0,
    DESTRUCTIBLE = 1,
    INDESTRUCTIBLE = 2
};

enum Action {
    MOVE_UP,
    MOVE_DOWN,
    MOVE_LEFT,
    MOVE_RIGHT,
    DROP_BOMB,
    NOOP
};

struct Pos {
    int r, c;
    bool operator==(const Pos &o) const { return r==o.r && c==o.c; }
};

struct Bomb {
    Pos p;
    int ownerId;      // 0 = player, 1 = bot
    int timer;        // ticks remaining; when reaches 0 -> explodes this tick
};

struct Player {
    Pos p;
    bool alive = true;
    int id; // 0 human, 1 bot
};

struct GameState {
    std::vector<std::vector<int>> grid; // grid[r][c] values 0/1/2
    Player players[2];
    std::vector<Bomb> bombs;
    int rows, cols;
    int tickCount = 0;

    // utilities
    bool inBounds(int r, int c) const;
    bool isFree(int r, int c) const; // free for moving (no wall, and no other player)
    std::optional<int> playerIndexAt(int r, int c) const; // returns index or nullopt
    void placeBomb(int owner, Pos p);
};

