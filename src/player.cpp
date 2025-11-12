#include "player.h"

Player::Player(int player_id, int r, int c)
    : id(player_id), pos({r, c}), is_alive(true), bomb_range(1) {}
