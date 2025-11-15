import heapq
from typing import Optional, List, Tuple, Set, Dict
from .map import GameMap
from .utils import manhattan, neighbors

def a_star(game_map: GameMap, start: Tuple[int,int], goal: Tuple[int,int], forbidden: Set[Tuple[int,int]]=set()) -> Optional[List[Tuple[int,int]]]:
    if start == goal:
        return []
    openh = []
    heapq.heappush(openh, (manhattan(start,goal), 0, start))
    came: Dict[Tuple[int,int], Tuple[int,int]] = {}
    gscore = {start: 0}
    closed = set()
    while openh:
        f,g,current = heapq.heappop(openh)
        if current in closed:
            continue
        if current == goal:
            path = []
            cur = current
            while cur != start:
                path.append(cur)
                cur = came[cur]
            path.reverse()
            return path
        closed.add(current)
        x,y = current
        for nx,ny in neighbors(current):
            if not game_map.in_bounds(nx,ny): continue
            if (nx,ny) in forbidden: continue
            tile = game_map.grid[ny][nx]
            if tile.ttype != 0: continue
            if tile.bomb is not None: continue
            tentative = g + 1
            if (nx,ny) not in gscore or tentative < gscore[(nx,ny)]:
                gscore[(nx,ny)] = tentative
                came[(nx,ny)] = current
                heapq.heappush(openh, (tentative + manhattan((nx,ny), goal), tentative, (nx,ny)))
    return None
