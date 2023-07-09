from __future__ import annotations

from typing import TYPE_CHECKING, Union, List

import numpy as np

from entities.game_map import GameMap
from entities.utils.enums import TurnState, Team

if TYPE_CHECKING:
    from entities.craftsman import Craftsman


class GameState:
    def __init__(self):
        self.map: Union[GameMap, None] = GameMap()
        self.craftsmen: List[Craftsman] = []
        self.turn_state = TurnState.INITIAL
        self.turn_number = 1

    def team1_craftsman_count(self):
        return len([c for c in self.craftsmen if c.team == Team.TEAM1])

    def team2_craftsman_count(self):
        return len([c for c in self.craftsmen if c.team == Team.TEAM2])
