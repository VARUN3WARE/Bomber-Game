"""Multiple pathfinding algorithms: A*, Dijkstra, and a simple JPS-like optimizer.

This module provides implementations that operate on the game's GameMap.
Each search returns the path (list of coordinates) and optionally the visited set
for visualization and metrics.
"""
from typing import List, Tuple, Optional, Set, Dict, Callable
import heapq
import time
from .utils import manhattan, neighbors
from .map import GameMap

def a_star_with_visited(game_map: GameMap, start: Tuple[int,int], goal: Tuple[int,int], forbidden: Set[Tuple[int,int]]=set()):
    """A* that also returns the visited nodes set for visualization."""
    if start == goal:
        return [], set()
    openh = []
    heapq.heappush(openh, (manhattan(start,goal), 0, start))
    came: Dict[Tuple[int,int], Tuple[int,int]] = {}
    gscore = {start: 0}
    closed = set()
    visited = set()
    while openh:
        f,g,current = heapq.heappop(openh)
        if current in closed:
            continue
        visited.add(current)
        if current == goal:
            path = []
            cur = current
            while cur != start:
                path.append(cur)
                cur = came[cur]
            path.reverse()
            return path, visited
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
    return None, visited

def dijkstra_with_visited(game_map: GameMap, start: Tuple[int,int], goal: Tuple[int,int], forbidden: Set[Tuple[int,int]]=set()):
    """Dijkstra's algorithm (uniform-cost) with visited set."""
    if start == goal:
        return [], set()
    openh = []
    heapq.heappush(openh, (0, start))
    came: Dict[Tuple[int,int], Tuple[int,int]] = {}
    dist = {start: 0}
    visited = set()
    closed = set()
    while openh:
        g,current = heapq.heappop(openh)
        if current in closed:
            continue
        visited.add(current)
        if current == goal:
            path = []
            cur = current
            while cur != start:
                path.append(cur)
                cur = came[cur]
            path.reverse()
            return path, visited
        closed.add(current)
        for nx,ny in neighbors(current):
            if not game_map.in_bounds(nx,ny): continue
            if (nx,ny) in forbidden: continue
            tile = game_map.grid[ny][nx]
            if tile.ttype != 0: continue
            if tile.bomb is not None: continue
            tentative = g + 1
            if (nx,ny) not in dist or tentative < dist[(nx,ny)]:
                dist[(nx,ny)] = tentative
                came[(nx,ny)] = current
                heapq.heappush(openh, (tentative, (nx,ny)))
    return None, visited

def jps_simple_with_visited(game_map: GameMap, start: Tuple[int,int], goal: Tuple[int,int], forbidden: Set[Tuple[int,int]]=set()):
    """A simplified Jump Point Search-like optimizer.

    This is not a full JPS implementation but acts as a jump-step pruner:
    when moving straight in cardinal directions, it "jumps" multiple tiles until
    an obstacle or the goal is reached, treating that landing as a neighbor.
    It greatly reduces node expansions on open corridors.
    Returns (path, visited).
    """
    if start == goal:
        return [], set()
    # We'll implement a priority queue search similar to A* but with pruned neighbors
    openh = []
    heapq.heappush(openh, (manhattan(start,goal), 0, start))
    came: Dict[Tuple[int,int], Tuple[int,int]] = {}
    gscore = {start: 0}
    closed = set()
    visited = set()

    def jump_line(x,y,dx,dy):
        # step along (dx,dy) until hitting obstacle or reaching goal; return last free cell
        steps = 0
        while True:
            nx = x + dx
            ny = y + dy
            if not game_map.in_bounds(nx,ny):
                return None
            tile = game_map.grid[ny][nx]
            if tile.ttype != 0 or tile.bomb is not None:
                return (x,y) if steps>0 else None
            steps += 1
            x,y = nx,ny
            if (x,y) == goal:
                return (x,y)
    while openh:
        f,g,current = heapq.heappop(openh)
        if current in closed:
            continue
        visited.add(current)
        if current == goal:
            path = []
            cur = current
            while cur != start:
                path.append(cur)
                cur = came[cur]
            path.reverse()
            return path, visited
        closed.add(current)
        x,y = current
        # consider jumps in 4 directions
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            j = jump_line(x,y,dx,dy)
            if j is None: continue
            nx,ny = j
            if (nx,ny) in forbidden: continue
            tentative = g + manhattan((x,y),(nx,ny))
            if (nx,ny) not in gscore or tentative < gscore[(nx,ny)]:
                gscore[(nx,ny)] = tentative
                came[(nx,ny)] = current
                heapq.heappush(openh, (tentative + manhattan((nx,ny), goal), tentative, (nx,ny)))
    return None, visited
