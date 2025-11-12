#include <iostream>
#include <vector>
#include <algorithm>
#include <limits>
#include "game.h"
#include "bot.h"

void print_game(const Game& game) {
    std::cout << "\nTick: " << game.tick_count << std::endl;
    for (int r = 0; r < game.board.rows; ++r) {
        for (int c = 0; c < game.board.cols; ++c) {
            Position current_pos = {r, c};
            
            bool is_explosion = false;
            for(const auto& site : game.explosion_sites) {
                if (site == current_pos) {
                    is_explosion = true;
                    break;
                }
            }

            if (is_explosion) {
                std::cout << "@ ";
                continue;
            }

            const Player* p = game.get_player_at(r, c);
            if (p) {
                std::cout << (p->id == 0 ? 'A' : 'X') << " ";
                continue;
            }

            bool is_bomb = false;
            for (const auto& bomb : game.bombs) {
                if (bomb.pos == current_pos) {
                    is_bomb = true;
                    break;
                }
            }
            if (is_bomb) {
                std::cout << "* ";
                continue;
            }

            switch (game.board.grid[r][c]) {
                case CELL_FREE:                std::cout << ". "; break;
                case CELL_DESTRUCTIBLE_WALL:   std::cout << "+ "; break;
                case CELL_INDESTRUCTIBLE_WALL: std::cout << "# "; break;
            }
        }
        std::cout << std::endl;
    }
    std::cout << "A=You, X=Bot, *=Bomb, @=Explosion, +=Destructible, #=Indestructible" << std::endl;
    std::cout << "Your health: " << (game.players[0].is_alive ? "ALIVE" : "DEAD") << std::endl;
    std::cout << "Bot health: " << (game.players[1].is_alive ? "ALIVE" : "DEAD") << std::endl;
}

Bot::Move get_player_move() {
    char input;
    while (true) {
        std::cout << "Enter move (w/a/s/d), b for bomb, p to pass: ";
        std::cin >> input;
        switch (input) {
            case 'w': return Bot::Move::UP;
            case 's': return Bot::Move::DOWN;
            case 'a': return Bot::Move::LEFT;
            case 'd': return Bot::Move::RIGHT;
            case 'b': return Bot::Move::BOMB;
            case 'p': return Bot::Move::NONE;
            default:
                std::cout << "Invalid input. Try again." << std::endl;
                std::cin.clear();
                std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        }
    }
}

int displayMenuAndGetDepth() {
    int depth;
    int choice;

    std::cout << "\n=== Configure Bot AI ===" << std::endl;
    std::cout << "Select Bot Difficulty:" << std::endl;
    std::cout << "1. Easy (Search Depth: 2)" << std::endl;
    std::cout << "2. Medium (Search Depth: 4)" << std::endl;
    std::cout << "3. Hard (Search Depth: 5)" << std::endl;
    std::cout << "Enter choice: ";
    
    while (!(std::cin >> choice) || choice < 1 || choice > 3) {
        std::cout << "Invalid input. Please enter 1, 2, or 3: ";
        std::cin.clear();
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    }

    switch(choice) {
        case 1:
            depth = 2;
            break;
        case 3:
            depth = 5;
            break;
        case 2:
        default:
            depth = 4;
            break;
    }
    
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    return depth;
}

int main() {
    Game game;
    
    int botSearchDepth = displayMenuAndGetDepth();

    while (!game.is_game_over()) {
        print_game(game);

        Bot::Move player_move = get_player_move();
        
        std::cout << "Bot is thinking..." << std::endl;
        Game bot_perspective_game = game;
        Bot::Move bot_move = Bot::get_best_move(bot_perspective_game, botSearchDepth);
        
        const char* bot_move_str = "NONE";
        switch(bot_move){
            case Bot::Move::UP: bot_move_str = "UP"; break;
            case Bot::Move::DOWN: bot_move_str = "DOWN"; break;
            case Bot::Move::LEFT: bot_move_str = "LEFT"; break;
            case Bot::Move::RIGHT: bot_move_str = "RIGHT"; break;
            case Bot::Move::BOMB: bot_move_str = "BOMB"; break;
            case Bot::Move::NONE: bot_move_str = "NONE"; break;
        }
        std::cout << "Bot chose: " << bot_move_str << std::endl;


        game.tick(player_move, bot_move);
    }

    print_game(game);
    int winner = game.get_winner();
    if (winner == 0) {
        std::cout << "You win!" << std::endl;
    } else if (winner == 1) {
        std::cout << "Bot wins!" << std::endl;
    } else {
        std::cout << "It's a draw!" << std::endl;
    }

    return 0;
}