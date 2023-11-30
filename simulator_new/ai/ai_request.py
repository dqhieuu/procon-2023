from enum import Enum
from typing import Any

from pydantic import BaseModel

class AIStrategyEnum(Enum):
    MANUAL = 'manual'
    EXPAND_TERRITORY = 'expand_territory'
    CAPTURE_CASTLE = 'capture_castle'
    SABOTAGE_OPPONENT = 'sabotage_opponent'
    PASSIVE_AGGRESSIVE = 'passive_aggressive'


class AIStrategyRequest(BaseModel):
    craftsman_id: str
    strategy: AIStrategyEnum
    detail: dict[str, Any]
