from copy import deepcopy
from functools import wraps
import time
from typing import List
from model import Direction


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(
            f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result

    return timeit_wrapper


def numpy_game_map_to_list_from_history(game_history: List):
    history = deepcopy(game_history)
    for turn in history:
        turn["state"].map.map = turn["state"].map.map.tolist()
    return history


def get_direction_vector(direction: Direction) -> tuple[int, int]:
    if direction == Direction.UP:
        return 0, -1
    elif direction == Direction.DOWN:
        return 0, 1
    elif direction == Direction.LEFT:
        return -1, 0
    elif direction == Direction.RIGHT:
        return 1, 0
    elif direction == Direction.UP_LEFT:
        return -1, -1
    elif direction == Direction.UP_RIGHT:
        return 1, -1
    elif direction == Direction.DOWN_LEFT:
        return -1, 1
    elif direction == Direction.DOWN_RIGHT:
        return 1, 1
