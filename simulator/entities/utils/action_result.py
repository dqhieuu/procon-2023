from __future__ import annotations

from copy import deepcopy
from enum import Enum

from entities.game_state import GameState
from entities.utils.enums import ActionType

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.craftman import Craftman


class FailCode(Enum):
    MOVE_DISTANCE_INVALID = 1
    MOVE_OUT_OF_MAP = 2
    MOVE_TO_POND = 3
    MOVE_TO_OPPONENT_WALL = 4
    MOVE_TO_CRAFTMAN_PREVIOUS_TURN_POS = 5
    MOVE_TO_CRAFTMAN_CURRENT_TURN_POS = 6
    BUILD_OUT_OF_MAP = 7
    BUILD_ON_NOT_PLAIN = 8
    BUILD_ON_CRAFTMAN = 9
    DESTROY_OUT_OF_MAP = 10
    DESTROY_NOT_WALL = 11


class FailError:
    def __init__(self, code: FailCode, message=""):
        self.code = code
        self.message = message


class ActionResult:
    def __init__(self,
                 action_type: ActionType,
                 success: bool,
                 actor_before: Craftman, actor_after: Craftman,
                 game_state_before: GameState, game_state_after: GameState,
                 action_detail=None,
                 fail_error: FailError | None = None
                 ):
        self.action_type = action_type
        self.action_detail = action_detail
        self.success = success
        self.actor_before = deepcopy(actor_before)
        self.actor_after = deepcopy(actor_after)
        self.game_state_before = deepcopy(game_state_before)
        self.game_state_after = deepcopy(game_state_after)
        self.fail_error = fail_error

    @classmethod
    def from_success(cls,
                     action_type: ActionType,
                     actor_before: Craftman, actor_after: Craftman,
                     game_state_before: GameState, game_state_after: GameState,
                     action_detail=None,
                     ):
        return cls(action_type, True, actor_before, actor_after, game_state_before, game_state_after, action_detail)

    @classmethod
    def from_fail(cls,
                  action_type: ActionType,
                  fail_error: FailError,
                  actor: Craftman,
                  game_state: GameState,
                  ):
        return cls(action_type,
                   success=False,
                   actor_before=actor, actor_after=actor,
                   game_state_before=game_state, game_state_after=game_state,
                   fail_error=fail_error)
