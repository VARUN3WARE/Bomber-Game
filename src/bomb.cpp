#include "bomb.h"

Bomb::Bomb(int r, int c, int owner, int bomb_range)
    : pos({r, c}), owner_id(owner), timer(BOMB_TIMER), range(bomb_range) {}
