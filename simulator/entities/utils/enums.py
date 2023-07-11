from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from online import OnlineEnumAction


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

    @staticmethod
    def from_online_type(online_type: str):
        if online_type == 'UPPER_LEFT':
            return Direction.UP_LEFT
        elif online_type == 'UPPER_RIGHT':
            return Direction.UP_RIGHT
        elif online_type == 'LOWER_LEFT':
            return Direction.DOWN_LEFT
        elif online_type == 'LOWER_RIGHT':
            return Direction.DOWN_RIGHT
        elif online_type in ['UP', 'ABOVE']:
            return Direction.UP
        elif online_type in ['DOWN', 'BELOW']:
            return Direction.DOWN
        elif online_type == 'LEFT':
            return Direction.LEFT
        elif online_type == 'RIGHT':
            return Direction.RIGHT
        else:
            return None




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

    @staticmethod
    def from_online_type(online_type: OnlineEnumAction):
        from online import OnlineEnumAction
        if online_type == OnlineEnumAction.STAY:
            return ActionType.STAY
        elif online_type == OnlineEnumAction.MOVE:
            return ActionType.MOVE
        elif online_type == OnlineEnumAction.BUILD:
            return ActionType.BUILD
        elif online_type == OnlineEnumAction.DESTROY:
            return ActionType.DESTROY
        else:
            raise ValueError("invalid online type")
