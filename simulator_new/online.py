from __future__ import annotations
import datetime
import json
from enum import Enum
from typing import List, Union

from pydantic import BaseModel, RootModel

from simulator_new.old import entities as ec, game
import simulator_new.old.entities.utils.enums as eue


class OnlineEnumSide(str, Enum):
    A = "A"
    B = "B"


class OnlineSide(BaseModel):
    side: OnlineEnumSide
    team_name: Union[str, None]
    team_id: Union[str, None]
    game_id: int
    id: int


class OnlinePos(BaseModel):
    x: int
    y: int


class OnlineCraftsman(BaseModel):
    x: int
    y: int
    side: OnlineEnumSide
    id: str


class OnlineField(BaseModel):
    id: int
    match_id: Union[int, None]
    name: str
    castle_coeff: int
    territory_coeff: int
    wall_coeff: int
    castles: List[OnlinePos]
    ponds: List[OnlinePos]
    width: int
    height: int
    craftsmen: List[OnlineCraftsman]


class OnlineFieldResponse(BaseModel):
    field: OnlineField
    field_id: int
    id: int
    name: str
    num_of_turns: int
    sides: List[OnlineSide]
    start_time: Union[datetime.datetime, None]
    time_per_turn: int


OnlineActionResponseList = RootModel[List[OnlineFieldResponse]]


class OnlineEnumAction(str, Enum):
    MOVE = "MOVE"
    BUILD = "BUILD"
    DESTROY = "DESTROY"
    STAY = "STAY"


class OnlineAction(BaseModel):
    action: OnlineEnumAction
    action_id: int
    action_param: Union[str, None]
    craftsman_id: str
    id: int


class OnlineActionResponse(BaseModel):
    turn: int
    team_id: int
    game_id: int
    id: int
    created_time: datetime.datetime
    actions: List[OnlineAction]


OnlineActionResponseList = RootModel[List[OnlineActionResponse]]


class OnlineGameStatus(BaseModel):
    cur_turn: int
    max_turn: int
    remaining: int


def local_command_to_online_action(command: ec.CraftsmanCommand, game_local: game.Game) -> dict[str, str]:
    craftsman = ec.get_craftsman_at(
        game_local.current_state.craftsmen, command.craftsman_pos)
    craftsman_id = craftsman.id

    if craftsman_id is None:
        raise Exception("Craftsman not found")

    online_command = {
        'craftsman_id': craftsman_id,
        'action': 'STAY'
    }

    if command.action_type is eue.ActionType.MOVE and command.direction in [eue.Direction.UP, eue.Direction.DOWN,
                                                                            eue.Direction.LEFT, eue.Direction.RIGHT,
                                                                            eue.Direction.UP_LEFT, eue.Direction.UP_RIGHT,
                                                                            eue.Direction.DOWN_LEFT, eue.Direction.DOWN_RIGHT]:
        online_command['action'] = 'MOVE'
        if command.direction == eue.Direction.UP:
            online_command['action_param'] = 'UP'
        elif command.direction == eue.Direction.DOWN:
            online_command['action_param'] = 'DOWN'
        elif command.direction == eue.Direction.LEFT:
            online_command['action_param'] = 'LEFT'
        elif command.direction == eue.Direction.RIGHT:
            online_command['action_param'] = 'RIGHT'
        elif command.direction == eue.Direction.UP_LEFT:
            online_command['action_param'] = 'UPPER_LEFT'
        elif command.direction == eue.Direction.UP_RIGHT:
            online_command['action_param'] = 'UPPER_RIGHT'
        elif command.direction == eue.Direction.DOWN_LEFT:
            online_command['action_param'] = 'LOWER_LEFT'
        elif command.direction == eue.Direction.DOWN_RIGHT:
            online_command['action_param'] = 'LOWER_RIGHT'
    elif command.action_type in [eue.ActionType.BUILD, eue.ActionType.DESTROY] and command.direction in [eue.Direction.UP,
                                                                                                         eue.Direction.DOWN,
                                                                                                         eue.Direction.LEFT,
                                                                                                         eue.Direction.RIGHT]:
        if command.action_type is eue.ActionType.BUILD:
            online_command['action'] = 'BUILD'
        elif command.action_type is eue.ActionType.DESTROY:
            online_command['action'] = 'DESTROY'

        if command.direction == eue.Direction.UP:
            online_command['action_param'] = 'ABOVE'
        elif command.direction == eue.Direction.DOWN:
            online_command['action_param'] = 'BELOW'
        elif command.direction == eue.Direction.LEFT:
            online_command['action_param'] = 'LEFT'
        elif command.direction == eue.Direction.RIGHT:
            online_command['action_param'] = 'RIGHT'

    return online_command


def online_field_decoder(obj):
    castles = obj.get("castles")
    if castles:
        obj["castles"] = json.loads(castles)

    ponds = obj.get("ponds")
    if ponds:
        obj["ponds"] = json.loads(ponds)

    craftsmen = obj.get("craftsmen")
    if craftsmen:
        obj["craftsmen"] = json.loads(craftsmen)
    return obj
