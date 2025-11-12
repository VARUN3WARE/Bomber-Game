#pragma once

#include "player.h"

const int BOMB_TIMER = 3;

struct Bomb {
    Position pos;
    int owner_id;
    int timer;
    int range;

    Bomb(int r, int c, int owner, int bomb_range);
};
