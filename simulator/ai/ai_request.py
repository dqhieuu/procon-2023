from enum import Enum

from pydantic import BaseModel


class AIStrategyRequest(BaseModel):
    craftsman_id: str
    strategy: str
    detail: dict[str, str]


class AIStrategyEnum(Enum):
    MANUAL = 'manual'
    EXPAND_TERRITORY = 'expand_territory'
    CAPTURE_CASTLE = 'capture_castle'
    SABOTAGE_OPPONENT = 'sabotage_opponent'
    PASSIVE_AGGRESSIVE = 'passive_aggressive'
