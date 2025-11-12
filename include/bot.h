#pragma once

#include "game.h"

namespace Bot {
    // Represents a potential move for the bot
    enum class Move {
        UP, DOWN, LEFT, RIGHT, BOMB, NONE
    };

    // Evaluates the current game state from the bot's perspective.
    // Higher score is better for the bot.
    int evaluate_state(const Game& game);

    // The main entry point for the bot's AI
    Move get_best_move(const Game& game, int depth);
}
