#pragma once

#include <vector>
#include <string>

enum CellType {
    CELL_FREE = 0,
    CELL_DESTRUCTIBLE_WALL = 1,
    CELL_INDESTRUCTIBLE_WALL = 2
};

struct Board {
    int rows;
    int cols;
    std::vector<std::vector<CellType>> grid;

    Board(int r = 0, int c = 0);
    void loadFromLayout(const std::vector<std::string>& layout);
    bool isWithinBounds(int r, int c) const;
};
