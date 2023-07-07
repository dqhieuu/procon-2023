from enum import Enum


class Team(Enum):
    TEAM1 = 'team1'
    TEAM2 = 'team2'
    NEUTRAL = 'neutral'


class TileType(Enum):
    PLAIN = 0
    CASTLE = 1
    POND = 2


class TerritoryType(Enum):
    OPEN = 'open'
    CLOSED = 'closed'
    NEUTRAL = 'neutral'


class TurnState(Enum):
    TEAM1_TURN = 'team1_turn'
    TEAM2_TURN = 'team2_turn'
    INITIAL = 'initial'
    GAME_OVER = 'game_over'


class Direction(str, Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'
    UP_LEFT = 'up_left'
    UP_RIGHT = 'up_right'
    DOWN_LEFT = 'down_left'
    DOWN_RIGHT = 'down_right'


def get_direction_vector(direction: Direction) -> (int, int):
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

def get_direction_from_vector(vector: (int, int)) -> Direction:
    x, y = vector
    if x == 0 and y == -1:
        return Direction.UP
    elif x == 0 and y == 1:
        return Direction.DOWN
    elif x == -1 and y == 0:
        return Direction.LEFT
    elif x == 1 and y == 0:
        return Direction.RIGHT
    elif x == -1 and y == -1:
        return Direction.UP_LEFT
    elif x == 1 and y == -1:
        return Direction.UP_RIGHT
    elif x == -1 and y == 1:
        return Direction.DOWN_LEFT
    elif x == 1 and y == 1:
        return Direction.DOWN_RIGHT


class ActionType(Enum):
    STAY = "stay"
    MOVE = "move"
    BUILD = "build"
    DESTROY = "destroy"
