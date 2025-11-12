#pragma once

struct Position {
    int r, c;

    bool operator==(const Position& other) const {
        return r == other.r && c == other.c;
    }
     bool operator!=(const Position& other) const {
        return !(*this == other);
    }
};

struct Player {
    int id;
    Position pos;
    bool is_alive;
    int bomb_range;

    Player(int player_id = 0, int r = 0, int c = 0);
};
