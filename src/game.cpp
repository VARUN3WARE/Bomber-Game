#include "game.h"
#include "bot.h"
#include <iostream>
#include <unordered_set>

// Helper for hashing Position for unordered_set
struct PositionHasher {
    std::size_t operator()(const Position& p) const {
        return std::hash<int>()(p.r) ^ (std::hash<int>()(p.c) << 1);
    }
};

Game::Game() : tick_count(0) {
    init();
}

void Game::init() {
    std::vector<std::string> layout = {
        "222222222222222",
        "2.............2",
        "2.2.1.2.1.2.1.2.2",
        "2.1.1.1.1.1.1.1.2",
        "2.1.2.1.2.1.2.1.2",
        "2...1...1...1...2",
        "2.1.2.1.2.1.2.1.2",
        "2.1.1.1.1.1.1.1.2",
        "2.2.1.2.1.2.1.2.2",
        "2.............2",
        "222222222222222"
    };
    board.loadFromLayout(layout);

    players[0] = Player(0, 1, 1);
    players[1] = Player(1, board.rows - 2, board.cols - 2);

    bombs.clear();
    explosion_sites.clear();
    tick_count = 0;
}

void Game::clear_explosions() {
    explosion_sites.clear();
}

void Game::tick(Bot::Move player_move, Bot::Move bot_move) {
    clear_explosions();

    apply_move(0, player_move);
    apply_move(1, bot_move);

    update_bombs();
    handle_explosions();

    tick_count++;
}

bool Game::is_game_over() const {
    return !players[0].is_alive || !players[1].is_alive;
}

int Game::get_winner() const {
    bool p0_alive = players[0].is_alive;
    bool p1_alive = players[1].is_alive;

    if (p0_alive && !p1_alive) return 0;
    if (!p0_alive && p1_alive) return 1;
    if (!p0_alive && !p1_alive) return 2; // Draw
    return -1; // Not over
}

bool Game::is_cell_free(int r, int c) const {
    if (!board.isWithinBounds(r, c)) return false;
    if (board.grid[r][c] != CELL_FREE) return false;
    if (get_player_at(r, c) != nullptr) return false;
    // Players can move over bombs
    return true;
}

bool Game::is_cell_safe(int r, int c) const {
    if (!board.isWithinBounds(r,c)) return false;

    for(const auto& bomb : bombs) {
        // Predict explosion for bombs about to go off
        if (bomb.timer <= 1) {
            // Check if the cell is on the same row and within horizontal range
            if (bomb.pos.r == r && std::abs(bomb.pos.c - c) <= bomb.range) {
                bool wall_between = false;
                int start_c = std::min(bomb.pos.c, c);
                int end_c = std::max(bomb.pos.c, c);
                for (int i = start_c; i < end_c; ++i) {
                    if (board.grid[r][i] == CELL_INDESTRUCTIBLE_WALL) {
                        wall_between = true;
                        break;
                    }
                }
                if (!wall_between) return false;
            }
            // Check if the cell is on the same col and within vertical range
            if (bomb.pos.c == c && std::abs(bomb.pos.r - r) <= bomb.range) {
                 bool wall_between = false;
                int start_r = std::min(bomb.pos.r, r);
                int end_r = std::max(bomb.pos.r, r);
                for (int i = start_r; i < end_r; ++i) {
                    if (board.grid[i][c] == CELL_INDESTRUCTIBLE_WALL) {
                        wall_between = true;
                        break;
                    }
                }
                if (!wall_between) return false;
            }
        }
    }
    return true;
}

Player* Game::get_player_at(int r, int c) {
    for (auto& player : players) {
        if (player.is_alive && player.pos.r == r && player.pos.c == c) {
            return &player;
        }
    }
    return nullptr;
}

const Player* Game::get_player_at(int r, int c) const {
    for (const auto& player : players) {
        if (player.is_alive && player.pos.r == r && player.pos.c == c) {
            return &player;
        }
    }
    return nullptr;
}

void Game::apply_move(int player_id, Bot::Move move) {
    if (!players[player_id].is_alive) return;

    Player& p = players[player_id];
    int dr = 0, dc = 0;

    switch (move) {
        case Bot::Move::UP:    dr = -1; break;
        case Bot::Move::DOWN:  dr = 1;  break;
        case Bot::Move::LEFT:  dc = -1; break;
        case Bot::Move::RIGHT: dc = 1;  break;
        case Bot::Move::BOMB: {
            bool bomb_exists = false;
            for(const auto& b : bombs) {
                if(b.pos.r == p.pos.r && b.pos.c == p.pos.c) {
                    bomb_exists = true;
                    break;
                }
            }
            if (!bomb_exists) {
                bombs.emplace_back(p.pos.r, p.pos.c, p.id, p.bomb_range);
            }
            return;
        }
        case Bot::Move::NONE:
            return;
    }

    int next_r = p.pos.r + dr;
    int next_c = p.pos.c + dc;

    if (is_cell_free(next_r, next_c)) {
        p.pos = {next_r, next_c};
    }
}

void Game::update_bombs() {
    for (auto& bomb : bombs) {
        if (bomb.timer > 0) {
            bomb.timer--;
        }
    }
}

void Game::handle_explosions() {
    clear_explosions(); // Clear sites from previous tick

    std::list<Bomb> exploding_now;
    
    // Initial trigger: find all bombs with timer <= 0
    bombs.remove_if([&](Bomb& bomb) {
        if (bomb.timer <= 0) {
            exploding_now.push_back(bomb);
            return true;
        }
        return false;
    });

    // Keep track of bombs that have exploded this tick to avoid re-triggering
    std::unordered_set<Position, PositionHasher> exploded_positions;

    while (!exploding_now.empty()) {
        Bomb current_bomb = exploding_now.front();
        exploding_now.pop_front();

        // Avoid processing the same bomb location twice in a chain
        if (exploded_positions.count(current_bomb.pos)) {
            continue;
        }
        exploded_positions.insert(current_bomb.pos);

        // 1. Calculate explosion sites for this bomb
        std::vector<Position> sites;
        // Center
        sites.push_back(current_bomb.pos);
        // Directions
        int dr[] = {-1, 1, 0, 0};
        int dc[] = {0, 0, -1, 1};
        for (int i = 0; i < 4; ++i) {
            for (int j = 1; j <= current_bomb.range; ++j) {
                int r = current_bomb.pos.r + dr[i] * j;
                int c = current_bomb.pos.c + dc[i] * j;
                if (!board.isWithinBounds(r, c)) break;
                if (board.grid[r][c] == CELL_INDESTRUCTIBLE_WALL) break;
                sites.push_back({r, c});
                if (board.grid[r][c] == CELL_DESTRUCTIBLE_WALL) break;
            }
        }

        // 2. Apply effects for these sites
        for (const auto& site : sites) {
            // Destroy walls
            if (board.isWithinBounds(site.r, site.c) && board.grid[site.r][site.c] == CELL_DESTRUCTIBLE_WALL) {
                board.grid[site.r][site.c] = CELL_FREE;
            }
            // Damage players
            for (auto& player : players) {
                if (player.is_alive && player.pos == site) {
                    // Bot (id 1) is immune to its own bombs (owner_id 1)
                    if (player.id == 1 && current_bomb.owner_id == 1) {
                        // Bot is immune to its own bomb, do nothing.
                    } else {
                        player.is_alive = false;
                    }
                }
            }
        }

        // 3. Check for chain reactions
        bombs.remove_if([&](Bomb& other_bomb) {
            for (const auto& site : sites) {
                if (other_bomb.pos == site) {
                    exploding_now.push_back(other_bomb);
                    return true;
                }
            }
            return false;
        });

        // Add sites for rendering
        explosion_sites.insert(explosion_sites.end(), sites.begin(), sites.end());
    }
}
