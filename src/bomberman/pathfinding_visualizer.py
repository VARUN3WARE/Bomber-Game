"""Helpers to run pathfinding algorithms and gather metrics for comparison and visualization."""
import time
from typing import Tuple, Callable, Dict, Any

def run_and_record(fn: Callable, game_map, start: Tuple[int,int], goal: Tuple[int,int], forbidden=set()) -> Dict[str, Any]:
    t0 = time.perf_counter()
    path, visited = fn(game_map, start, goal, forbidden)
    t1 = time.perf_counter()
    nodes = len(visited) if visited is not None else 0
    return {
        'path': path,
        'visited': visited,
        'nodes_explored': nodes,
        'time_ms': (t1 - t0) * 1000.0,
    }
