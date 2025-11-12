#include "board.h"

Board::Board(int r, int c) : rows(r), cols(c) {
    if (r > 0 && c > 0) {
        grid.assign(r, std::vector<CellType>(c, CELL_FREE));
    }
}

void Board::loadFromLayout(const std::vector<std::string>& layout) {
    rows = layout.size();
    if (rows == 0) {
        cols = 0;
        return;
    }
    cols = layout[0].size();
    grid.assign(rows, std::vector<CellType>(cols, CELL_FREE));

    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            switch (layout[r][c]) {
                case '1':
                    grid[r][c] = CELL_DESTRUCTIBLE_WALL;
                    break;
                case '2':
                    grid[r][c] = CELL_INDESTRUCTIBLE_WALL;
                    break;
                default:
                    grid[r][c] = CELL_FREE;
                    break;
            }
        }
    }
}

bool Board::isWithinBounds(int r, int c) const {
    return r >= 0 && r < rows && c >= 0 && c < cols;
}
