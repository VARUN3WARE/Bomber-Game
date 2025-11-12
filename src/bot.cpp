#include "bot.h"
#include <algorithm>
#include <vector>

namespace Bot {

    struct AlphaBetaResult {
        int score;
        Move move;
    };

    // Forward declaration
    AlphaBetaResult alphabeta(Game game, int depth, int alpha, int beta, bool is_maximizing);

    // NEW "Run and Hide" evaluation logic
    int evaluate_state(const Game& game) {
        if (game.is_game_over()) {
            int winner = game.get_winner();
            if (winner == 1) return 100000; // Bot survives (wins)
            if (winner == 0) return -100000; // Bot dies (loses)
            return 0; // Draw
        }

        auto dist = [&](const Position &a, const Position &b){
            return abs(a.r-b.r) + abs(a.c-b.c);
        };

        int sc = 0;
        const Player& bot = game.players[1];
        const Player& human = game.players[0];

        if (!bot.is_alive) return -100000;

        // Objective 1: Maximize distance from the human player
        int d = dist(bot.pos, human.pos);
        sc += d * 10;

        // Objective 2: Maximize walls between self and human
        int walls_between = 0;
        int r_min = std::min(bot.pos.r, human.pos.r);
        int r_max = std::max(bot.pos.r, human.pos.r);
        int c_min = std::min(bot.pos.c, human.pos.c);
        int c_max = std::max(bot.pos.c, human.pos.c);
        for (int r = r_min; r <= r_max; ++r) {
            for (int c = c_min; c <= c_max; ++c) {
                if (game.board.grid[r][c] != CELL_FREE) {
                    walls_between++;
                }
            }
        }
        sc += walls_between * 5; // More walls is better

        // Objective 3: Avoid bombs
        for (const auto &b : game.bombs) {
            if (b.owner_id == 0 && b.timer <= 2) { // Look ahead for safety
                int dToBot = dist(b.pos, bot.pos);
                if (dToBot <= b.range) {
                    bool hasEscape = false;
                    Position up = {bot.pos.r-1, bot.pos.c}, down = {bot.pos.r+1, bot.pos.c}, left = {bot.pos.r, bot.pos.c-1}, right = {bot.pos.r, bot.pos.c+1};
                    if (game.is_cell_free(up.r, up.c) && dist(up, b.pos) > b.range) hasEscape = true;
                    if (!hasEscape && game.is_cell_free(down.r, down.c) && dist(down, b.pos) > b.range) hasEscape = true;
                    if (!hasEscape && game.is_cell_free(left.r, left.c) && dist(left, b.pos) > b.range) hasEscape = true;
                    if (!hasEscape && game.is_cell_free(right.r, right.c) && dist(right, b.pos) > b.range) hasEscape = true;
                    
                    if (!hasEscape) {
                        sc -= 1000; // Heavy penalty for being trapped by a player's bomb
                    }
                }
            }
        }
        return sc;
    }

    Move get_best_move(const Game& game, int depth) {
        AlphaBetaResult result = alphabeta(game, depth, -100000, 100000, true);
        return result.move;
    }

    // NEW: Bot (player 1) can no longer place bombs
    std::vector<Move> get_legal_moves(const Game& game, int player_id) {
        std::vector<Move> moves;
        if (!game.players[player_id].is_alive) {
            moves.push_back(Move::NONE);
            return moves;
        }
        
        if (player_id == 0) { // Only human player can drop bombs
            moves.push_back(Move::BOMB);
        }

        moves.push_back(Move::NONE);
        Position p = game.players[player_id].pos;
        if (game.is_cell_free(p.r - 1, p.c)) moves.push_back(Move::UP);
        if (game.is_cell_free(p.r + 1, p.c)) moves.push_back(Move::DOWN);
        if (game.is_cell_free(p.r, p.c - 1)) moves.push_back(Move::LEFT);
        if (game.is_cell_free(p.r, p.c + 1)) moves.push_back(Move::RIGHT);
        return moves;
    }

    // Search algorithm remains the same, but uses the new evaluation function
    AlphaBetaResult alphabeta(Game game, int depth, int alpha, int beta, bool is_maximizing) {
        if (depth == 0 || game.is_game_over()) {
            return {evaluate_state(game), Move::NONE};
        }

        if (is_maximizing) { // Bot's turn
            int max_eval = -100000;
            Move best_move = Move::NONE;
            auto bot_moves = get_legal_moves(game, 1);

            for (Move move : bot_moves) {
                Game next_game_state = game;
                next_game_state.apply_move(1, move);
                int eval = alphabeta(next_game_state, depth - 1, alpha, beta, false).score;

                // Add a small penalty for standing still to encourage movement
                if (move == Move::NONE) {
                    eval -= 2;
                }

                if (eval > max_eval) {
                    max_eval = eval;
                    best_move = move;
                } 
                // Tie-breaking: Prefer any move over standing still
                else if (eval == max_eval && best_move == Move::NONE) {
                    best_move = move;
                }

                alpha = std::max(alpha, eval);
                if (beta <= alpha) {
                    break;
                }
            }
            return {max_eval, best_move};
        } else { // Player's turn
            int min_eval = 100000;
            Move best_move = Move::NONE;
            auto human_moves = get_legal_moves(game, 0);

            for (Move move : human_moves) {
                Game next_game_state = game;
                next_game_state.apply_move(0, move);
                
                // After both players move, tick the game state
                next_game_state.update_bombs();
                next_game_state.handle_explosions();
                next_game_state.tick_count++;

                int eval = alphabeta(next_game_state, depth - 1, alpha, beta, true).score;
                 if (eval < min_eval) {
                    min_eval = eval;
                    best_move = move;
                }
                beta = std::min(beta, eval);
                if (beta <= alpha) {
                    break;
                }
            }
            return {min_eval, best_move};
        }
    }
}
