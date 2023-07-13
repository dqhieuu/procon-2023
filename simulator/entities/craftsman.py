import secrets
from copy import copy
from typing import Union, List

from pydantic import BaseModel

from entities.game_state import GameState
from entities.utils.action_result import ActionResult, FailError, FailCode
from entities.utils.enums import Team, ActionType, Direction


class CraftsmanCommand(BaseModel):
    craftsman_pos: tuple[int, int]
    action_type: ActionType
    direction: Union[Direction,None] = None


# Different actions per craftsmans turn: 1 + 8 + 4 + 4 = 17
# All 4 craftsman actions have no side effects
class Craftsman:
    def __init__(self, team: Team, pos: tuple[int, int], id=None):
        self.team = team
        self.pos = pos
        # dependencies
        self.phase_start_game_state: Union[GameState, None] = None
        self.latest_action_game_state: Union[GameState, None] = None
        self.has_committed_action = False
        self.id = id if id is not None else secrets.token_hex(8)

    def __eq__(self, other):
        return self.team == other.team and self.pos == other.pos and self.id == other.id

    def stay(self) -> ActionResult:
        self.__check_prerequisites()
        return ActionResult.from_success(
            action_type=ActionType.STAY,
            actor_before=self, actor_after=self,
            game_state_before=self.latest_action_game_state, game_state_after=self.latest_action_game_state
        )

    def move(self, direction: tuple[int, int]) -> ActionResult:
        self.__check_prerequisites()

        if abs(direction[0]) > 1 or abs(direction[1]) > 1 or direction == (0, 0):
            raise ValueError("Invalid move direction")

        next_pos = (self.pos[0] + direction[0], self.pos[1] + direction[1])
        if not self.phase_start_game_state.map.is_valid_pos(*next_pos):
            return ActionResult.from_fail(
                action_type=ActionType.MOVE,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.MOVE_OUT_OF_MAP,
                                     message="Move from {} to {} is out of map (max: ({}))"
                                     .format(self.pos,
                                             next_pos,
                                             (self.phase_start_game_state.map.width,
                                              self.phase_start_game_state.map.height)
                                             )),
            )

        if has_craftsman_at(self.phase_start_game_state.craftsmen, next_pos):
            return ActionResult.from_fail(
                action_type=ActionType.MOVE,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.MOVE_TO_CRAFTSMAN_PREVIOUS_TURN_POS,
                                     message="{} to {} is occupied by other craftsman from previous turn".format(
                                         self.pos, next_pos)),
            )

        if has_craftsman_at(self.latest_action_game_state.craftsmen, next_pos):
            return ActionResult.from_fail(
                action_type=ActionType.MOVE,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.MOVE_TO_CRAFTSMAN_CURRENT_TURN_POS,
                                     message="{} to {} is occupied by other craftsman from current turn".format(
                                         self.pos, next_pos)),
            )

        next_pos_tile = self.latest_action_game_state.map.get_tile(*next_pos)
        if next_pos_tile.has_pond:
            return ActionResult.from_fail(
                action_type=ActionType.MOVE,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.MOVE_TO_POND,
                                     message="{} to {} is a pond".format(self.pos, next_pos)),
            )

        if (next_pos_tile.wall == Team.TEAM1 and self.team == Team.TEAM2) or (
                next_pos_tile.wall == Team.TEAM2 and self.team == Team.TEAM1):
            return ActionResult.from_fail(
                action_type=ActionType.MOVE,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.MOVE_TO_OPPONENT_WALL,
                                     message="{} to {} is opponent's team wall".format(self.pos, next_pos)),
            )

        craftsman_after_move = self.without_game_state()
        craftsman_after_move.pos = next_pos

        # logic will be wrong, but it's for the sake of performance
        # game_state_after_move = deepcopy(self.latest_action_game_state)
        game_state_after_move = self.latest_action_game_state
        game_state_after_move.craftsmen.remove(self)
        game_state_after_move.craftsmen.append(craftsman_after_move)

        return ActionResult.from_success(
            action_type=ActionType.MOVE,
            actor_before=self, actor_after=craftsman_after_move,
            game_state_before=self.latest_action_game_state, game_state_after=game_state_after_move,
            action_detail="{} moved from {} to {}".format(self, self.pos, next_pos)
        )

    def build(self, direction: tuple[int, int]) -> ActionResult:
        self.__check_prerequisites()

        move_dist = abs(direction[0]) + abs(direction[1])
        if move_dist > 1 or move_dist == 0:
            raise ValueError("Invalid build direction")

        next_pos = (self.pos[0] + direction[0], self.pos[1] + direction[1])
        if not self.latest_action_game_state.map.is_valid_pos(*next_pos):
            return ActionResult.from_fail(
                action_type=ActionType.BUILD,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.BUILD_OUT_OF_MAP,
                                     message="Build at {} is out of map (max: ({},{}))"
                                     .format(next_pos,
                                             self.latest_action_game_state.map.width,
                                             self.latest_action_game_state.map.height)),
            )

        next_pos_tile = self.latest_action_game_state.map.get_tile(*next_pos)
        if next_pos_tile.has_pond or next_pos_tile.has_castle:
            return ActionResult.from_fail(
                action_type=ActionType.BUILD,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.BUILD_ON_NOT_PLAIN,
                                     message="Build at {} is not plain type tile".format(next_pos)),
            )

        if has_craftsman_at(self.latest_action_game_state.craftsmen, next_pos):
            return ActionResult.from_fail(
                action_type=ActionType.BUILD,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.BUILD_ON_CRAFTSMAN,
                                     message="Can't build at {} because it's occupied by an craftsman".format(
                                         next_pos)),
            )

        if (next_pos_tile.wall == Team.TEAM1 and self.team == Team.TEAM2) or (next_pos_tile.wall == Team.TEAM2 and self.team == Team.TEAM1):
            return ActionResult.from_fail(
                action_type=ActionType.BUILD,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.BUILD_ON_OPPONENT_WALL,
                                     message="Can't build at {} because it's opponent's team wall".format(
                                         next_pos)),
            )

        selected_tile_with_wall_built = copy(next_pos_tile)
        selected_tile_with_wall_built.wall = Team.TEAM1 if self.team == Team.TEAM1 else Team.TEAM2

        # logic will be wrong, but it's for the sake of performance
        # cloned_game_state = deepcopy(self.latest_action_game_state)
        cloned_game_state = self.latest_action_game_state
        cloned_game_state.map.set_tile(*next_pos, selected_tile_with_wall_built)

        return ActionResult.from_success(
            action_type=ActionType.BUILD,
            actor_before=self, actor_after=self,
            game_state_before=self.latest_action_game_state,
            game_state_after=cloned_game_state,
            action_detail="{} built wall at {}".format(self, next_pos),
        )

    def destroy(self, direction: tuple[int, int]) -> ActionResult:
        self.__check_prerequisites()

        move_dist = abs(direction[0]) + abs(direction[1])
        if move_dist > 1 or move_dist == 0:
            raise ValueError("Invalid build direction")

        next_pos = (self.pos[0] + direction[0], self.pos[1] + direction[1])
        if not self.latest_action_game_state.map.is_valid_pos(*next_pos):
            return ActionResult.from_fail(
                action_type=ActionType.DESTROY,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.DESTROY_OUT_OF_MAP,
                                     message="Destroy at {} is out of map (max: ({},{}))"
                                     .format(next_pos,
                                             self.latest_action_game_state.map.width,
                                             self.latest_action_game_state.map.height)),
            )

        next_pos_tile = self.latest_action_game_state.map.get_tile(*next_pos)
        if next_pos_tile.wall == Team.NEUTRAL:
            return ActionResult.from_fail(
                action_type=ActionType.DESTROY,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.DESTROY_NOT_WALL,
                                     message="Destroy at {} is not wall type tile".format(next_pos)),
            )

        selected_tile_with_wall_destroyed = copy(next_pos_tile)
        selected_tile_with_wall_destroyed.wall = Team.NEUTRAL

        # logic will be wrong, but it's for the sake of performance
        # cloned_game_state = deepcopy(self.latest_action_game_state)
        cloned_game_state = self.latest_action_game_state
        cloned_game_state.map.set_tile(*next_pos, selected_tile_with_wall_destroyed)

        return ActionResult.from_success(
            action_type=ActionType.BUILD,
            actor_before=self, actor_after=self,
            game_state_before=self.latest_action_game_state,
            game_state_after=cloned_game_state,
            action_detail="{} destroyed wall at {}".format(self, next_pos),
        )

    def with_game_state(self, phase_start_game_state: GameState, latest_action_game_state: GameState):
        clone = copy(self)
        clone.phase_start_game_state = phase_start_game_state
        clone.latest_action_game_state = latest_action_game_state
        return clone

    def without_game_state(self):
        clone = copy(self)
        clone.phase_start_game_state = None
        clone.latest_action_game_state = None
        return clone

    def __check_prerequisites(self):
        if self.phase_start_game_state is None:
            raise Exception("phase_start_game_state is not set")
        if self.latest_action_game_state is None:
            raise Exception("latest_action_game_state is not set")


def has_craftsman_at(list_of_craftsmen: List[Craftsman], pos: tuple[int, int]) -> bool:
    for craftsman in list_of_craftsmen:
        if craftsman.pos == pos:
            return True
    return False


def get_craftsman_at(list_of_craftsmen: List[Craftsman], pos: tuple[int, int]) -> Union[Craftsman, None]:
    for craftsman in list_of_craftsmen:
        if craftsman.pos == pos:
            return craftsman
    return None
