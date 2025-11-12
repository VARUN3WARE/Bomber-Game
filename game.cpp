// game.cpp
#include "game.h"
#include <algorithm>

bool GameState::inBounds(int r, int c) const {
    return r>=0 && r<rows && c>=0 && c<cols;
}

std::optional<int> GameState::playerIndexAt(int r, int c) const {
    for (int i=0;i<2;i++){
        if (players[i].alive && players[i].p.r==r && players[i].p.c==c) return i;
    }
    return std::nullopt;
}

bool GameState::isFree(int r, int c) const {
    if (!inBounds(r,c)) return false;
    if (grid[r][c] != FREE) return false;
    if (playerIndexAt(r,c).has_value()) return false;
    // bombs do not block movement in this simplified version (common in bomberman); adjust if needed
    return true;
}

void GameState::placeBomb(int owner, Pos p) {
    // don't place if there's already a bomb in that cell
    for (auto &b : bombs) {
        if (b.p == p) return;
    }
    Bomb nb;
    nb.p = p;
    nb.ownerId = owner;
    nb.timer = 2; // as per spec: takes 2 ticks to explode
    bombs.push_back(nb);
}

