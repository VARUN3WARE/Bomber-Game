#pragma once

#include <vector>
#include <list>
#include "board.h"
#include "player.h"
#include "bomb.h"

// Forward-declare Bot::Move to break circular dependency
namespace Bot {
    enum class Move;
}

class Game {
public:
    Board board;
    Player players[2]; // 0 = human, 1 = bot
    std::list<Bomb> bombs;
    std::vector<Position> explosion_sites;
    int tick_count;

    Game();

    void init();
    void tick(Bot::Move player_move, Bot::Move bot_move);
    void clear_explosions();

    bool is_game_over() const;
    int get_winner() const; // -1 for no winner yet, 0 for player, 1 for bot, 2 for draw

    bool is_cell_free(int r, int c) const;
    bool is_cell_safe(int r, int c) const;
    Player* get_player_at(int r, int c);
    const Player* get_player_at(int r, int c) const;

    void apply_move(int player_id, Bot::Move move);
    void update_bombs();
    void handle_explosions();


private:
    
};
