from __future__ import annotations
import datetime
import json
from enum import Enum
from typing import Union, List

from pydantic import BaseModel, RootModel
from bin.game_interfaces_binding import Craftsman, Game, GameAction, GameOptions, TileMask

from model import CraftsmanCommand, Direction, OnlineEnumAction, PyActionType
from utils_cpp import online_action_to_cpp_action


class OnlineEnumSide(str, Enum):
    A = "A"
    B = "B"


class OnlineSide(BaseModel):
    side: OnlineEnumSide
    team_name: Union[str, None]
    team_id: Union[int, None]
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


OnlineFieldRequestList = RootModel[List[OnlineFieldResponse]]


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


def local_command_to_online_action(command: CraftsmanCommand, game: Game, craftsman_strid_to_intid: dict[str, int]) -> dict[str, str]:
    craftsman_intid_to_strid = {v: k for k,
                                v in craftsman_strid_to_intid.items()}

    current_state = game.getCurrentState()
    craftsman_id = current_state.findCraftsmanIdByPos(*command.craftsman_pos)
    craftsman_str_id = craftsman_intid_to_strid[craftsman_id]

    if craftsman_id is None:
        raise Exception("Craftsman not found")

    online_command = {
        'craftsman_id': craftsman_str_id,
        'action': 'STAY'
    }

    if command.action_type is PyActionType.MOVE and command.direction in [Direction.UP, Direction.DOWN,
                                                                          Direction.LEFT, Direction.RIGHT,
                                                                          Direction.UP_LEFT, Direction.UP_RIGHT,
                                                                          Direction.DOWN_LEFT, Direction.DOWN_RIGHT]:
        online_command['action'] = 'MOVE'
        if command.direction == Direction.UP:
            online_command['action_param'] = 'UP'
        elif command.direction == Direction.DOWN:
            online_command['action_param'] = 'DOWN'
        elif command.direction == Direction.LEFT:
            online_command['action_param'] = 'LEFT'
        elif command.direction == Direction.RIGHT:
            online_command['action_param'] = 'RIGHT'
        elif command.direction == Direction.UP_LEFT:
            online_command['action_param'] = 'UPPER_LEFT'
        elif command.direction == Direction.UP_RIGHT:
            online_command['action_param'] = 'UPPER_RIGHT'
        elif command.direction == Direction.DOWN_LEFT:
            online_command['action_param'] = 'LOWER_LEFT'
        elif command.direction == Direction.DOWN_RIGHT:
            online_command['action_param'] = 'LOWER_RIGHT'
    elif command.action_type in [PyActionType.BUILD, PyActionType.DESTROY] and command.direction in [Direction.UP,
                                                                                                     Direction.DOWN,
                                                                                                     Direction.LEFT,
                                                                                                     Direction.RIGHT]:
        if command.action_type is PyActionType.BUILD:
            online_command['action'] = 'BUILD'
        elif command.action_type is PyActionType.DESTROY:
            online_command['action'] = 'DESTROY'

        if command.direction == Direction.UP:
            online_command['action_param'] = 'ABOVE'
        elif command.direction == Direction.DOWN:
            online_command['action_param'] = 'BELOW'
        elif command.direction == Direction.LEFT:
            online_command['action_param'] = 'LEFT'
        elif command.direction == Direction.RIGHT:
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


def load_online_game(field: OnlineFieldResponse) -> tuple[GameOptions, list[list[int]], list[Craftsman], dict[str, int], dict[int, str]]:
    go = GameOptions()
    go.mapWidth = field.field.width
    go.mapHeight = field.field.height
    go.maxTurns = field.num_of_turns
    go.castleCoeff = field.field.castle_coeff
    go.territoryCoeff = field.field.territory_coeff
    go.wallCoeff = field.field.wall_coeff

    game_map = [[0 for _ in range(go.mapWidth)] for _ in range(go.mapHeight)]
    for pond in field.field.ponds:
        game_map[pond.y][pond.x] |= 1 << TileMask.POND.value
    for castle in field.field.castles:
        game_map[castle.y][castle.x] |= 1 << TileMask.CASTLE.value

    craftsman_strid_to_intid = {}
    craftsmen: list[Craftsman] = []

    counter = 0
    for craftsman in field.field.craftsmen:
        craftsman_strid_to_intid[craftsman.id] = counter
        craftsmen.append(Craftsman(
            counter, craftsman.x, craftsman.y, craftsman.side == OnlineEnumSide.A))
        counter += 1
    
    crafstman_intid_to_strid = {v: k for k, v in craftsman_strid_to_intid.items()}

    return go, game_map, craftsmen, craftsman_strid_to_intid, crafstman_intid_to_strid


def load_online_actions(actions_list: List[OnlineActionResponse], craftsman_strid_to_intid_map: dict[str, int]) -> dict[int, list[GameAction]]:
    actions: dict[int, list[GameAction]] = {}
    for action_group in actions_list:
        for action in action_group.actions:
            craftsman_id = craftsman_strid_to_intid_map[action.craftsman_id]
            cpp_action, cpp_subaction = online_action_to_cpp_action(
                action.action.value, action.action_param)
            game_action = GameAction(craftsman_id, cpp_action, cpp_subaction)

            actions[action_group.turn] = game_action

    return actions
