import datetime
import json
from enum import Enum
from typing import List

from pydantic import BaseModel


class OnlineEnumSide(str, Enum):
    A = "A"
    B = "B"


class OnlineSide(BaseModel):
    side: OnlineEnumSide
    team_name: str
    team_id: int
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
    match_id: int
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
    start_time: datetime.datetime
    time_per_turn: int


class OnlineFieldRequestList(BaseModel):
    __root__: List[OnlineFieldResponse]


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


class OnlineEnumAction(str, Enum):
    MOVE = "MOVE"
    BUILD = "BUILD"
    DESTROY = "DESTROY"
    STAY = "STAY"


class OnlineAction(BaseModel):
    action: OnlineEnumAction
    action_id: int
    action_param: str
    craftsman_id: str
    id: int


class OnlineActionResponse(BaseModel):
    turn: int
    team_id: int
    game_id: int
    id: int
    created_time: datetime.datetime
    actions: List[OnlineAction]


class OnlineActionResponseList(BaseModel):
    __root__: List[OnlineActionResponse]


class OnlineGameStatus(BaseModel):
    cur_turn: int
    max_turn: int
    remaining: int
