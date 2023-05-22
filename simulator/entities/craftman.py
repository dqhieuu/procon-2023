from copy import deepcopy

from pydantic import BaseModel

from entities.game_state import GameState
from entities.utils.action_result import ActionResult, FailError, FailCode
from entities.utils.enums import Team, TileType, ActionType, Direction


class CraftmanCommand(BaseModel):
    craftman_pos: tuple[int, int]
    action_type: ActionType
    direction: Direction | None = None


# Different actions per craftmans turn: 1 + 8 + 4 + 4 = 17
# All 4 craftman actions have no side effects
class Craftman:
    def __init__(self, team: Team, pos: tuple[int, int]):
        self.team = team
        self.pos = pos
        # dependencies
        self.phase_start_game_state: GameState | None = None
        self.latest_action_game_state: GameState | None = None

    def __eq__(self, other):
        return self.team == other.team and self.pos == other.pos

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

        if has_craftman_at(self.phase_start_game_state.craftmen, next_pos):
            return ActionResult.from_fail(
                action_type=ActionType.MOVE,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.MOVE_TO_CRAFTMAN_PREVIOUS_TURN_POS,
                                     message="{} to {} is occupied by other craftman from previous turn".format(
                                         self.pos, next_pos)),
            )

        if has_craftman_at(self.latest_action_game_state.craftmen, next_pos):
            return ActionResult.from_fail(
                action_type=ActionType.MOVE,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.MOVE_TO_CRAFTMAN_CURRENT_TURN_POS,
                                     message="{} to {} is occupied by other craftman from current turn".format(
                                         self.pos, next_pos)),
            )

        next_pos_tile = self.latest_action_game_state.map.get_tile(*next_pos)
        if next_pos_tile.type == TileType.POND:
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

        craftman_after_move = self.without_game_state()
        craftman_after_move.pos = next_pos

        game_state_after_move = deepcopy(self.latest_action_game_state)
        game_state_after_move.craftmen.remove(self)
        game_state_after_move.craftmen.append(craftman_after_move)

        return ActionResult.from_success(
            action_type=ActionType.MOVE,
            actor_before=self, actor_after=craftman_after_move,
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
        if next_pos_tile.type != TileType.PLAIN:
            return ActionResult.from_fail(
                action_type=ActionType.BUILD,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.BUILD_ON_NOT_PLAIN,
                                     message="Build at {} is not plain type tile".format(next_pos)),
            )

        if has_craftman_at(self.latest_action_game_state.craftmen, next_pos):
            return ActionResult.from_fail(
                action_type=ActionType.BUILD,
                actor=self,
                game_state=self.latest_action_game_state,
                fail_error=FailError(code=FailCode.BUILD_ON_CRAFTMAN,
                                     message="Can't build at {} because it's occupied by an craftman".format(
                                         next_pos)),
            )

        selected_tile_with_wall_built = deepcopy(next_pos_tile)
        selected_tile_with_wall_built.wall = Team.TEAM1 if self.team == Team.TEAM1 else Team.TEAM2

        cloned_game_state = deepcopy(self.latest_action_game_state)
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

        selected_tile_with_wall_destroyed = deepcopy(next_pos_tile)
        selected_tile_with_wall_destroyed.wall = Team.NEUTRAL

        cloned_game_state = deepcopy(self.latest_action_game_state)
        cloned_game_state.map.set_tile(*next_pos, selected_tile_with_wall_destroyed)

        return ActionResult.from_success(
            action_type=ActionType.BUILD,
            actor_before=self, actor_after=self,
            game_state_before=self.latest_action_game_state,
            game_state_after=cloned_game_state,
            action_detail="{} destroyed wall at {}".format(self, next_pos),
        )

    def with_game_state(self, phase_start_game_state: GameState, latest_action_game_state: GameState):
        clone = deepcopy(self)
        clone.phase_start_game_state = phase_start_game_state
        clone.latest_action_game_state = latest_action_game_state
        return clone

    def without_game_state(self):
        clone = deepcopy(self)
        clone.phase_start_game_state = None
        clone.latest_action_game_state = None
        return clone

    def __check_prerequisites(self):
        if self.phase_start_game_state is None:
            raise Exception("phase_start_game_state is not set")
        if self.latest_action_game_state is None:
            raise Exception("latest_action_game_state is not set")


def has_craftman_at(list_of_craftmen: list[Craftman], pos: tuple[int, int]) -> bool:
    for craftman in list_of_craftmen:
        if craftman.pos == pos:
            return True
    return False


def get_craftman_at(list_of_craftmen: list[Craftman], pos: tuple[int, int]) -> Craftman | None:
    for craftman in list_of_craftmen:
        if craftman.pos == pos:
            return craftman
    return None
