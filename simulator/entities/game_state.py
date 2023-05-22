from __future__ import annotations

from entities.game_map import GameMap
from entities.tile import Tile
from entities.utils.enums import TurnState, Team

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.craftman import Craftman


class GameState:
    def __init__(self):
        self.map: GameMap | None = GameMap()
        self.craftmen: list[Craftman] = []
        self.turn_state = TurnState.TEAM1_TURN
        self.turn_number = 1
