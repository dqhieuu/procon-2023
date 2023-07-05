import functools
import os
from copy import deepcopy
from typing import Optional

import numpy as np

from entities.craftsman import CraftsmanCommand, get_craftsman_at, Craftsman
from entities.game_map import ScoreCoefficients
from entities.game_state import GameState
from entities.tile import Tile
from entities.utils.enums import ActionType, get_direction_vector, Team, TurnState, Direction
from score_compute import get_territory_computed_map, compute_score


class Game:
    def __init__(self, map_path: str):
        self.current_state = GameState()
        self.history: list[GameState] = [self.current_state]
        self.command_buffer: list[CraftsmanCommand] = []

        self.score_coefficients = ScoreCoefficients(territory=1, wall=1, castle=1)
        self.max_turn = 0
        self.load_map(map_path)



    def categorize_and_deduplicate_commands_from_buffer(self):
        craftsman_pos_dict = {}
        result: dict[str, list[CraftsmanCommand]] = {
            "move": [],
            "build": [],
            "destroy": []
        }
        # one craftsman pos can only have one command
        for command in self.command_buffer:
            craftsman_pos_dict[command.craftsman_pos] = command
        for command in craftsman_pos_dict.values():
            if command.action_type == ActionType.MOVE:
                result["move"].append(command)
            elif command.action_type == ActionType.BUILD:
                result["build"].append(command)
            elif command.action_type == ActionType.DESTROY:
                result["destroy"].append(command)

        return result

    def load_map(self, file_path):
        # print("Current working directory: " + os.getcwd())
        with open('/mnt/f/procon-2023/simulator/pettingzoo-environment/MARLlib/{}'.format(file_path), "r") as f:
        # with open('F:/procon-2023/simulator/assets/map2.txt'.format(file_path), "r") as f:
            self._reset_game_state()
            mode = ""
            for line in f:
                line = line.strip()
                if line == "":
                    continue
                elif line == "map" or line == "team1" or line == "team2":
                    mode = line
                    continue
                elif line.startswith("territory"):
                    mode = "score_coefficients"
                    self.score_coefficients.territory = int(line.split(" ")[1])
                elif line.startswith("wall"):
                    mode = "score_coefficients"
                    self.score_coefficients.wall = int(line.split(" ")[1])
                elif line.startswith("castle"):
                    mode = "score_coefficients"
                    self.score_coefficients.castle = int(line.split(" ")[1])
                elif line.startswith("turns"):
                    mode = "turns"
                    self.max_turn = int(line.split(" ")[1])

                if mode == "map":
                    if self.current_state.map.map is None:
                        self.current_state.map.map = np.empty((0, len(line)), dtype=Tile)
                    self.current_state.map.map = np.vstack((self.current_state.map.map, [Tile.from_file_string(tile) for tile in list(line)]))
                elif mode == "team1" or mode == "team2":
                    pos = list(map(int, line.split(" ")))
                    self.current_state.craftsmen.append(
                        Craftsman(Team.TEAM1 if mode == "team1" else Team.TEAM2, (pos[0], pos[1])))

    @property
    def is_game_over(self):
        return self.current_state.turn_number > self.max_turn

    def add_command(self, command: CraftsmanCommand):
        if self.is_game_over:
            return
        craftsman = get_craftsman_at(self.current_state.craftsmen, command.craftsman_pos)
        if craftsman is not None:
            craftsman.has_committed_action = True

        self.command_buffer.append(command)

    def _agent_name_to_craftsman(self, agent: str) -> Optional[Craftsman]:
        team = Team.TEAM1 if agent.startswith("team1") else Team.TEAM2
        craftsman_index = int(agent.split("_")[1].replace("craftsman", "")) - 1
        craftsman_of_team = [c for c in self.current_state.craftsmen if c.team == team]
        if craftsman_index >= len(craftsman_of_team):
            return None
        return craftsman_of_team[craftsman_index]

    # agent is "team{1|2}_craftsman{1-based index}"
    def gym_add_command(self, agent: str, command: int):
        craftsman = self._agent_name_to_craftsman(agent)
        if craftsman is None:
            return
        if command == 0:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.STAY))
        elif command == 1:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE,
                                              direction=Direction.UP))
        elif command == 2:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE,
                                              direction=Direction.DOWN))
        elif command == 3:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE,
                                              direction=Direction.LEFT))
        elif command == 4:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE,
                                              direction=Direction.RIGHT))
        elif command == 5:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE
                                              , direction=Direction.UP_LEFT))
        elif command == 6:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE
                                              , direction=Direction.UP_RIGHT))
        elif command == 7:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE
                                              , direction=Direction.DOWN_LEFT))
        elif command == 8:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE
                                              , direction=Direction.DOWN_RIGHT))
        elif command == 9:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.BUILD,
                                              direction=Direction.UP))
        elif command == 10:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.BUILD,
                                              direction=Direction.DOWN))
        elif command == 11:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.BUILD,
                                              direction=Direction.LEFT))
        elif command == 12:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.BUILD,
                                              direction=Direction.RIGHT))
        elif command == 13:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY
                                              , direction=Direction.UP))
        elif command == 14:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY
                                              , direction=Direction.DOWN))
        elif command == 15:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY
                                              , direction=Direction.LEFT))
        elif command == 16:
            self.add_command(CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY
                                              , direction=Direction.RIGHT))

    @property
    def gym_observable_space(self) -> np.ndarray:
        map = self.current_state.map
        craftman_t1_pos_exist = set()
        craftman_t2_pos_exist = set()
        for craftsman in self.current_state.craftsmen:
            if craftsman.team == Team.TEAM1:
                craftman_t1_pos_exist.add(craftsman.pos)
            else:
                craftman_t2_pos_exist.add(craftsman.pos)

        # Add committed craftsman to distinguish between uncommitted craftsman and committed craftsman
        craftman_tcur_action_committed = set()
        for craftsman in self.current_state.craftsmen:
            if ((craftsman.team == Team.TEAM1 and self.current_state.turn_state == TurnState.TEAM1_TURN)
                    or (craftsman.team == Team.TEAM2 and self.current_state.turn_state == TurnState.TEAM2_TURN)):
                if craftsman.has_committed_action:
                    craftman_tcur_action_committed.add(craftsman.pos)

        width = map.width
        height = map.height
        arr = np.zeros((height, width, 12), dtype=bool)

        for y in range(height):
            for x in range(width):
                tile = map.get_tile(x, y)
                arr[y][x][0] = (x, y) in craftman_t1_pos_exist
                arr[y][x][1] = (x, y) in craftman_t2_pos_exist
                arr[y][x][2] = tile.wall == Team.TEAM1
                arr[y][x][3] = tile.wall == Team.TEAM2
                arr[y][x][4] = tile.has_castle
                arr[y][x][5] = tile.has_pond
                arr[y][x][6] = tile.is_team1_closed_territory
                arr[y][x][7] = tile.is_team2_closed_territory
                arr[y][x][8] = tile.is_team1_open_territory
                arr[y][x][9] = tile.is_team2_open_territory
                arr[y][x][10] = self.current_state.turn_state == TurnState.TEAM2_TURN
                arr[y][x][11] = (x, y) in craftman_tcur_action_committed

        return arr.flatten()

    def process_turn(self):
        if self.is_game_over:
            return
        commands = self.categorize_and_deduplicate_commands_from_buffer()
        self.command_buffer.clear()

        command_res = []

        phase_start_state = deepcopy(self.current_state)
        prev_turn_state = phase_start_state
        self.history.append(phase_start_state)

        for command in commands["destroy"]:
            selected = get_craftsman_at(phase_start_state.craftsmen, command.craftsman_pos)
            if selected is not None:
                if can_select_piece(selected.team, phase_start_state.turn_state) is False:
                    command_res.append("Cannot select enemy craftsman (at {})".format(command.craftsman_pos))
                    continue
                selected = selected.with_game_state(phase_start_state, self.current_state)
                res = selected.destroy(get_direction_vector(command.direction))
                command_res.append(res)
                if res.success:
                    self.current_state = res.game_state_after

        phase_start_state = deepcopy(self.current_state)
        for command in commands["build"]:
            selected = get_craftsman_at(phase_start_state.craftsmen, command.craftsman_pos)
            if selected is not None:
                if can_select_piece(selected.team, phase_start_state.turn_state) is False:
                    command_res.append("Cannot select enemy craftsman (at {})".format(command.craftsman_pos))
                    continue
                selected = selected.with_game_state(phase_start_state, self.current_state)
                res = selected.build(get_direction_vector(command.direction))
                command_res.append(res)
                if res.success:
                    self.current_state = res.game_state_after

        phase_start_state = deepcopy(self.current_state)
        for command in commands["move"]:
            selected = get_craftsman_at(phase_start_state.craftsmen, command.craftsman_pos)
            if selected is not None:
                if can_select_piece(selected.team, phase_start_state.turn_state) is False:
                    command_res.append("Cannot select enemy craftsman (at {})".format(command.craftsman_pos))
                    continue
                selected = selected.with_game_state(phase_start_state, self.current_state)
                res = selected.move(get_direction_vector(command.direction))
                command_res.append(res)
                if res.success:
                    self.current_state = res.game_state_after

        # compute territory
        territory_computed_map = get_territory_computed_map(prev_turn_state.map, self.current_state.map)
        self.current_state.map = territory_computed_map

        self.current_state.turn_number += 1
        self.current_state.turn_state = TurnState.TEAM1_TURN if self.current_state.turn_state == TurnState.TEAM2_TURN else TurnState.TEAM2_TURN

        # set has_commited_action to False for all craftsmen
        for craftsman in self.current_state.craftsmen:
            craftsman.has_committed_action = False

        return command_res

    @property
    def score(self):
        return compute_score(self.current_state.map, self.score_coefficients)

    @property
    def winning_team(self):
        score = self.score
        print(score)
        t1_score = score['team1']
        t2_score = score['team2']
        # Team with the highest total score wins
        t1_total = t1_score['points']['total']
        t2_total = t2_score['points']['total']
        if t1_total > t2_total:
            return Team.TEAM1
        elif t2_total > t1_total:
            return Team.TEAM2

        # Else, team with the highest castle score wins
        t1_castle = t1_score['points']['castle']
        t2_castle = t2_score['points']['castle']
        if t1_castle > t2_castle:
            return Team.TEAM1
        elif t2_castle > t1_castle:
            return Team.TEAM2

        # Else, team with the highest territory score wins
        t1_territory = t1_score['points']['territory']
        t2_territory = t2_score['points']['territory']
        if t1_territory > t2_territory:
            return Team.TEAM1
        elif t2_territory > t1_territory:
            return Team.TEAM2

        # Else, no one wins (this differs from the original rules)
        return Team.NEUTRAL

    @property
    def score_difference(self):
        score = self.score
        return score['team1']['points']['total'] - score['team2']['points']['total']

    def _reset_game_state(self):
        self.current_state = GameState()
        self.history = [self.current_state]
        self.command_buffer.clear()


def can_select_piece(piece_team: Team, turn_state: TurnState):
    return (piece_team == Team.TEAM1 and turn_state == TurnState.TEAM1_TURN) or \
        (piece_team == Team.TEAM2 and turn_state == TurnState.TEAM2_TURN)
