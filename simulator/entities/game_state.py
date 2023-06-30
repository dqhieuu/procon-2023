from __future__ import annotations

from typing import TYPE_CHECKING, Union

from entities.game_map import GameMap
from entities.utils.enums import TurnState

if TYPE_CHECKING:
    from entities.craftsman import Craftsman


class GameState:
    def __init__(self):
        self.map: Union[GameMap, None] = GameMap()
        self.craftsmen: list[Craftsman] = []
        self.turn_state = TurnState.TEAM1_TURN
        self.turn_number = 1
