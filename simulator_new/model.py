from enum import Enum
from typing import Union, List

from pydantic import BaseModel

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

class OnlineEnumAction(str, Enum):
    MOVE = "MOVE"
    BUILD = "BUILD"
    DESTROY = "DESTROY"
    STAY = "STAY"

class ActionTypeServer(Enum):
    STAY = "stay"
    MOVE = "move"
    BUILD = "build"
    DESTROY = "destroy"

    @staticmethod
    def from_online_type(online_type: OnlineEnumAction):
        from online import OnlineEnumAction
        if online_type == OnlineEnumAction.STAY:
            return ActionTypeServer.STAY
        elif online_type == OnlineEnumAction.MOVE:
            return ActionTypeServer.MOVE
        elif online_type == OnlineEnumAction.BUILD:
            return ActionTypeServer.BUILD
        elif online_type == OnlineEnumAction.DESTROY:
            return ActionTypeServer.DESTROY
        else:
            raise ValueError("invalid online type")

class CraftsmanCommand(BaseModel):
    craftsman_pos: tuple[int, int]
    action_type: ActionTypeServer
    direction: Union[Direction,None] = None




