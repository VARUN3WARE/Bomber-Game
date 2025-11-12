// main.cpp
#include <bits/stdc++.h>
#include <limits>
#include "game.h"
using namespace std;

/*
Simple console-based Bomberman simulation.
Controls:
  w/a/s/d - move up/left/down/right
  b       - drop bomb
  q       - quit
Each input counts as one action for the player; then bot acts; then game advances 1 tick.
*/

static const vector<pair<int,int>> DIRS = {
    {-1,0}, {1,0}, {0,-1}, {0,1}
};

string cellChar(const GameState &G, int r, int c) {
    // Represent cell for console:
    // '.' free, '#' indestructible, '+' destructible, 'P' player, 'B' bot, '*' bomb
    auto pi = G.playerIndexAt(r,c);
    if (pi.has_value()) {
        return (pi.value()==0) ? "A" : "X";
    }
    for (auto &b : G.bombs) {
        if (b.p.r==r && b.p.c==c) return "*";
    }
    if (G.grid[r][c]==FREE) return ".";
    if (G.grid[r][c]==DESTRUCTIBLE) return "+";
    return "#";
}

void printGame(const GameState &G) {
#ifdef _WIN32
    system("cls");
#else
    system("clear");
#endif
    cout << "Tick: " << G.tickCount << "\n";
    for (int r=0;r<G.rows;r++){
        for (int c=0;c<G.cols;c++){
            cout << cellChar(G,r,c) << ' ';
        }
        cout << '\n';
    }
    cout << "Controls: w/a/s/d to move, b to drop bomb, q to quit\n";
    cout << "A = you, X = bot, * = bomb, + destructible, # indestructible\n";
}

// apply move for a given player id; returns true if action used (for recording)
bool applyAction(GameState &G, int pid, Action a) {
    if (!G.players[pid].alive) return false;
    Pos cur = G.players[pid].p;
    if (a==DROP_BOMB) {
        G.placeBomb(pid, cur);
        return true;
    } else if (a==NOOP) {
        return true;
    }
    int dr=0, dc=0;
    if (a==MOVE_UP) { dr=-1; dc=0; }
    if (a==MOVE_DOWN) { dr=1; dc=0; }
    if (a==MOVE_LEFT) { dr=0; dc=-1; }
    if (a==MOVE_RIGHT) { dr=0; dc=1; }
    int nr=cur.r+dr, nc=cur.c+dc;
    if (G.inBounds(nr,nc) && G.isFree(nr,nc)) {
        G.players[pid].p.r=nr;
        G.players[pid].p.c=nc;
        return true;
    }
    return false;
}

// explosion helper: apply explosion at given position and mark destroyed walls and affected players
void explodeAt(GameState &G, const Pos &p) {
    // positions to clear/damage: centre + 1 cell each direction (3 cells wide including center)
    auto hit = [&](int r, int c){
        if (!G.inBounds(r,c)) return;
        // destroy destructible wall
        if (G.grid[r][c] == DESTRUCTIBLE) {
            G.grid[r][c] = FREE;
        }
        // kill players there
        for (int i=0;i<2;i++){
            if (G.players[i].alive && G.players[i].p.r==r && G.players[i].p.c==c) {
                G.players[i].alive = false;
            }
        }
    };
    // center
    hit(p.r, p.c);
    // four directions, length 1 each (since total 3 cells)
    const int ranges = 1;
    for (auto d : DIRS) {
        for (int step=1; step<=ranges; ++step) {
            int nr = p.r + d.first*step;
            int nc = p.c + d.second*step;
            if (!G.inBounds(nr,nc)) break;
            if (G.grid[nr][nc] == INDESTRUCTIBLE) {
                // blocked, stop propagation
                break;
            }
            hit(nr,nc);
            if (G.grid[nr][nc] == DESTRUCTIBLE) {
                // explosion stops after destroying destructible tile
                break;
            }
        }
    }
}

// advance bombs by one tick, exploding those whose timer reaches 0. chain-reactions handled.
void tickBombs(GameState &G) {
    // First decrease timers
    for (auto &b : G.bombs) b.timer--;
    // Explode all bombs with timer <= 0; but chain reactions: explosions may trigger bombs -> loop until stable
    bool something = true;
    while (something) {
        something = false;
        vector<Bomb> remaining;
        vector<Pos> toExplode;
        for (auto &b : G.bombs) {
            if (b.timer <= 0) {
                toExplode.push_back(b.p);
                something = true;
            } else {
                remaining.push_back(b);
            }
        }
        G.bombs.swap(remaining); // remove exploded bombs
        for (auto &pos : toExplode) {
            // before calling explodeAt, also trigger bombs located in explosion tiles: we must set them to explode immediately
            // But since we removed bombs at timer<=0, remaining bombs with timer>0 could be in explosion range; handle by scanning G.bombs and setting their timer=0 if in range
            // We'll explodeAt first (which may clear destructible walls and kill players)
            explodeAt(G, pos);
            // find bombs in range -> set timer to 0 to explode in this same while loop iteration
            vector<Bomb> newRemaining;
            for (auto &b : G.bombs) {
                bool triggered = false;
                // check if b.p within center or one step away
                if (abs(b.p.r - pos.r) + abs(b.p.c - pos.c) == 0) triggered = true;
                else if (b.p.r == pos.r && abs(b.p.c - pos.c) == 1) triggered = true;
                else if (b.p.c == pos.c && abs(b.p.r - pos.r) == 1) triggered = true;
                if (triggered) {
                    b.timer = 0;
                }
                newRemaining.push_back(b);
            }
            G.bombs.swap(newRemaining);
        }
    }
}

// Evaluate a state for the bot (higher = better for bot)
int evaluateForBot(const GameState &G) {
    // terminal checks
    if (!G.players[1].alive && !G.players[0].alive) return 0;
    if (!G.players[0].alive) return 100000; // bot wins
    if (!G.players[1].alive) return -100000; // bot dead - bad

    auto dist = [&](const Pos &a, const Pos &b){
        return abs(a.r-b.r) + abs(a.c-b.c);
    };
    int sc = 0;
    int d = dist(G.players[1].p, G.players[0].p);
    sc += (50 - d*5); // closer is better

    // fewer destructible walls left gives small bonus (encourage clearing)
    int destructibleLeft = 0;
    for (int r=0;r<G.rows;r++) for (int c=0;c<G.cols;c++) if (G.grid[r][c]==DESTRUCTIBLE) destructibleLeft++;
    sc += (30 - destructibleLeft);

    // Encourage threatening the player and penalize self-danger
    for (auto &b : G.bombs) {
        int dToBot = dist(b.p, G.players[1].p);
        int dToPlayer = dist(b.p, G.players[0].p);

        // If it's the bot's bomb, give a bonus for placing it near the player
        if (b.ownerId == 1 && dToPlayer <= 1) {
             sc += 25; // Bonus for placing a threatening bomb
        }

        // If any bomb is about to explode, evaluate risk/reward
        if (b.timer <= 1) {
            if (dToBot <= 1) {
                // The bot is in the blast radius. Check for an escape route.
                bool hasEscape = false;
                Pos cur = G.players[1].p;
                Pos up = {cur.r-1, cur.c}, down = {cur.r+1, cur.c}, left = {cur.r, cur.c-1}, right = {cur.r, cur.c+1};

                if (G.isFree(up.r, up.c) && dist(up, b.p) > 1) hasEscape = true;
                if (!hasEscape && G.isFree(down.r, down.c) && dist(down, b.p) > 1) hasEscape = true;
                if (!hasEscape && G.isFree(left.r, left.c) && dist(left, b.p) > 1) hasEscape = true;
                if (!hasEscape && G.isFree(right.r, right.c) && dist(right, b.p) > 1) hasEscape = true;
                
                if (hasEscape) {
                    sc -= 20; // In a risky spot, but has an escape. Minor penalty.
                } else {
                    sc -= 200; // Trapped! Major penalty.
                }
            }
            if (dToPlayer <= 1) {
                // Check if player is trapped
                 bool playerHasEscape = false;
                Pos cur = G.players[0].p;
                Pos up = {cur.r-1, cur.c}, down = {cur.r+1, cur.c}, left = {cur.r, cur.c-1}, right = {cur.r, cur.c+1};

                if (G.isFree(up.r, up.c) && dist(up, b.p) > 1) playerHasEscape = true;
                if (!playerHasEscape && G.isFree(down.r, down.c) && dist(down, b.p) > 1) playerHasEscape = true;
                if (!playerHasEscape && G.isFree(left.r, left.c) && dist(left, b.p) > 1) playerHasEscape = true;
                if (!playerHasEscape && G.isFree(right.r, right.c) && dist(right, b.p) > 1) playerHasEscape = true;

                if (playerHasEscape) {
                    sc += 50; // Good if opponent is threatened.
                } else {
                    sc += 200; // Excellent if opponent is trapped.
                }
            }
        }
    }
    return sc;
}

// generate legal actions for player id in this state
vector<Action> legalActions(const GameState &G, int pid) {
    vector<Action> acts;
    if (!G.players[pid].alive) return {NOOP};
    // moves
    Pos cur = G.players[pid].p;
    if (G.isFree(cur.r-1, cur.c)) acts.push_back(MOVE_UP);
    if (G.isFree(cur.r+1, cur.c)) acts.push_back(MOVE_DOWN);
    if (G.isFree(cur.r, cur.c-1)) acts.push_back(MOVE_LEFT);
    if (G.isFree(cur.r, cur.c+1)) acts.push_back(MOVE_RIGHT);
    // drop bomb always possible (we allow multiple bombs placed)
    acts.push_back(DROP_BOMB);
    acts.push_back(NOOP);
    return acts;
}

// we need to simulate a tick given actions for both players: apply player action then opponent action, then tick bombs.
void simulateTick(GameState &S, Action humanAct, Action botAct) {
    // apply human
    applyAction(S, 0, humanAct);
    // apply bot
    applyAction(S, 1, botAct);
    // advance bombs (decrease timers and explode)
    tickBombs(S);
    S.tickCount++;
}

// For the bot: depth limited minimax with alpha-beta. We will treat the bot as maximizing.
struct ABResult { int value; Action bestAction; };

ABResult alphabeta(GameState state, int depth, int alpha, int beta, bool maximizingPlayer) {
    // terminal conditions
    if (depth==0 || !state.players[0].alive || !state.players[1].alive) {
        int val = evaluateForBot(state);
        return {val, NOOP};
    }
    if (maximizingPlayer) {
        int bestVal = -1000000;
        Action bestAct = NOOP;
        auto actions = legalActions(state, 1); // bot moves
        for (auto a : actions) {
            GameState copy = state;
            // In the search, we model turns sequentially.
            // Bot makes a move, then human makes a move, then the world ticks.
            // So, just apply the bot's move to the state.
            applyAction(copy, 1, a);
            // Then, find the human's best response to this state.
            auto res = alphabeta(copy, depth-1, alpha, beta, false);
            if (res.value > bestVal) {
                bestVal = res.value;
                bestAct = a;
            }
            alpha = max(alpha, bestVal);
            if (beta <= alpha) break;
        }
        return {bestVal, bestAct};
    } else {
        // minimizing = human's turn; they react to the state with the bot's move already applied.
        int bestVal = 1000000;
        Action bestAct = NOOP;
        auto actions = legalActions(state, 0);
        for (auto a : actions) {
            GameState after_human_move = state;
            // Apply the human's move. Now both moves for the tick are applied.
            applyAction(after_human_move, 0, a);
            // Now, we can tick the bombs and advance the game state.
            tickBombs(after_human_move);
            after_human_move.tickCount++;
            // And evaluate the resulting state from the bot's perspective for the next turn.
            auto res = alphabeta(after_human_move, depth-1, alpha, beta, true);
            if (res.value < bestVal) {
                bestVal = res.value;
                bestAct = a;
            }
            beta = min(beta, bestVal);
            if (beta <= alpha) break;
        }
        return {bestVal, bestAct};
    }
}

int displayMenuAndGetDepth() {
    int depth;
    int choice;

    cout << "\n=== Configure Bot AI ===" << endl;
    cout << "Select Bot Difficulty:" << endl;
    cout << "1. Easy (Search Depth: 2)" << endl;
    cout << "2. Medium (Search Depth: 4)" << endl;
    cout << "3. Hard (Search Depth: 5)" << endl;
    cout << "Enter choice: ";
    
    while (!(cin >> choice) || choice < 1 || choice > 3) {
        cout << "Invalid input. Please enter 1, 2, or 3: ";
        cin.clear();
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
    }

    switch(choice) {
        case 1:
            depth = 2;
            break;
        case 3:
            depth = 5; // Using 5 instead of 6 to keep it a bit faster
            break;
        case 2:
        default:
            depth = 4;
            break;
    }
    
    // Clear the rest of the line from the input buffer
    cin.ignore(numeric_limits<streamsize>::max(), '\n');

    return depth;
}

Action getBotAction(const GameState &G, int searchDepth) {
    // simple depth-limited search with alpha-beta
    auto res = alphabeta(G, searchDepth, -1000000, 1000000, true);
    return res.bestAction;
}

// read user input and map to action
Action parseHumanInput(char ch) {
    if (ch=='w' || ch=='W') return MOVE_UP;
    if (ch=='s' || ch=='S') return MOVE_DOWN;
    if (ch=='a' || ch=='A') return MOVE_LEFT;
    if (ch=='d' || ch=='D') return MOVE_RIGHT;
    if (ch=='b' || ch=='B') return DROP_BOMB;
    return NOOP;
}

GameState makeSampleGame() {
    // sample small map
    vector<string> layout = {
        "2222222",
        "2.1.1.2",
        "2.....2",
        "2.1.1.2",
        "2.....2",
        "2.1.1.2",
        "2222222"
    };
    int R = (int)layout.size();
    int C = (int)layout[0].size();
    GameState G;
    G.rows = R; G.cols = C;
    G.grid.assign(R, vector<int>(C, FREE));
    for (int r=0;r<R;r++) for (int c=0;c<C;c++){
        char ch = layout[r][c];
        if (ch=='2') G.grid[r][c] = INDESTRUCTIBLE;
        else if (ch=='1') G.grid[r][c] = DESTRUCTIBLE;
        else G.grid[r][c] = FREE;
    }
    G.players[0].p = {2,1}; G.players[0].alive = true; G.players[0].id = 0;
    G.players[1].p = {4,5}; G.players[1].alive = true; G.players[1].id = 1;
    G.bombs.clear();
    G.tickCount = 0;
    return G;
}

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cout << "=== Simple Bomberman Simulation ===\n";
    
    int botSearchDepth = displayMenuAndGetDepth();

    GameState G = makeSampleGame();
    printGame(G);
    while (true) {
        if (!G.players[0].alive) {
            cout << "You died. Game over.\n";
            break;
        }
        if (!G.players[1].alive) {
            cout << "Bot dead. You win!\n";
            break;
        }
        cout << "Enter action (w/a/s/d = move, b = bomb, q = quit): ";
        string s;
        if (!getline(cin,s)) break;
        if (s.size()>0 && (s[0]=='q' || s[0]=='Q')) {
            cout << "Quitting.\n";
            break;
        }
        Action humanAct = NOOP;
        if (s.size()>0) humanAct = parseHumanInput(s[0]);

        // Bot chooses action using search on current real state
        cout << "Bot is thinking..." << endl;
        Action botAct = getBotAction(G, botSearchDepth);

        // Now simulate a real tick: apply player then bot then bombs (this ordering matches implementation)
        simulateTick(G, humanAct, botAct);

        printGame(G);
    }
    return 0;
}

