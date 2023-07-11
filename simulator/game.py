from __future__ import annotations
import threading
from datetime import datetime
from copy import deepcopy
from typing import Optional, List, TYPE_CHECKING
from fastapi.encoders import jsonable_encoder

import numpy as np
import json

import entities.craftsman
from entities.score_coeff import ScoreCoefficients

from entities.utils.enums import ActionType, get_direction_vector, Team, TurnState, Direction
import score_compute
from online import OnlineEnumSide, OnlineFieldResponse, OnlineActionResponseList, OnlineGameStatus
from utils import numpy_game_map_to_list_from_history

from entities.tile import Tile
from entities.game_state import GameState


def save_game_history(game_history):
    json_compatible_history = jsonable_encoder(numpy_game_map_to_list_from_history(game_history))
    with open("history/game_{}.json".format(datetime.now().strftime("%Y-%m-%d_%H.%M.%S")), "w") as file:
        json.dump(json_compatible_history, file, separators=(',', ':'))


class Game:
    def __init__(self, map_path: str = None):
        self.current_state = GameState()
        self.history: List = []
        self.command_buffer: List[entities.craftsman.CraftsmanCommand] = []

        self.score_coefficients = ScoreCoefficients(territory=1, wall=1, castle=1)
        self.max_turn = 0
        if map_path is not None:
            self.load_map(map_path)

    def categorize_and_deduplicate_commands_from_buffer(self):
        craftsman_pos_dict = {}
        result: dict[str, List[entities.craftsman.CraftsmanCommand]] = {
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
        # with open('/mnt/f/procon-2023/simulator/pettingzoo-environment/MARLlib/{}'.format(file_path), "r") as f:
        with open(file_path, "r") as f:
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
                    self.current_state.map.map = np.vstack(
                        (self.current_state.map.map, [Tile.from_file_string(tile) for tile in list(line)]))
                elif mode == "team1" or mode == "team2":
                    pos = list(map(int, line.split(" ")))
                    self.current_state.craftsmen.append(
                        entities.craftsman.Craftsman(Team.TEAM1 if mode == "team1" else Team.TEAM2, (pos[0], pos[1])))

    def load_online_action_list(self, action_list: OnlineActionResponseList, current_game_status: OnlineGameStatus = None):
        if self.is_game_over:
            return

        online_actions = sorted(action_list.__root__, key=lambda x: (x.turn, x.created_time))
        action_by_turn = {}
        for online_action in online_actions:
            action_by_turn[online_action.turn - 1] = online_action
        apply_until_reach_turn = current_game_status.cur_turn if current_game_status is not None else self.max_turn+1

        while self.current_state.turn_number < apply_until_reach_turn:
            if action_by_turn.get(self.current_state.turn_number) is not None:
                for online_action in action_by_turn[self.current_state.turn_number].actions:
                    craftsman = self.find_craftsman_by_id(online_action.craftsman_id)
                    action_type = ActionType.from_online_type(online_action.action)
                    direction = Direction.from_online_type(online_action.action_param)
                    craftsman_command = entities.craftsman.CraftsmanCommand(
                        craftsman_pos=craftsman.pos,
                        action_type=action_type,
                        direction=direction,
                    )

                    self.add_command(craftsman_command)
            self.process_turn()

    def load_online_map(self, field_data: OnlineFieldResponse):
        self._reset_game_state()
        self.max_turn = field_data.num_of_turns
        self.score_coefficients = ScoreCoefficients(
            territory=field_data.field.territory_coeff,
            wall=field_data.field.wall_coeff,
            castle=field_data.field.castle_coeff
        )

        self.current_state.map.map = np.array([Tile() for _ in range(field_data.field.width * field_data.field.height)])
        self.current_state.map.map = self.current_state.map.map.reshape((field_data.field.height, field_data.field.width))

        for craftsman in field_data.field.craftsmen:
            self.current_state.craftsmen.append(
                entities.craftsman.Craftsman(team=Team.TEAM1 if craftsman.side == OnlineEnumSide.A else Team.TEAM2,
                                             pos=(craftsman.x, craftsman.y), id=craftsman.id)
            )
        for castle_pos in field_data.field.castles:
            self.current_state.map.get_tile(castle_pos.x, castle_pos.y).has_castle = True
        for pond_pos in field_data.field.ponds:
            self.current_state.map.get_tile(pond_pos.x, pond_pos.y).has_pond = True

    @property
    def is_game_over(self):
        return self.current_state.turn_number > self.max_turn

    def add_command(self, command: entities.craftsman.CraftsmanCommand):
        if self.is_game_over:
            return
        craftsman = entities.craftsman.get_craftsman_at(self.current_state.craftsmen, command.craftsman_pos)
        if craftsman is not None:
            craftsman.has_committed_action = True

        self.command_buffer.append(command)

    def find_craftsman_by_id(self, craftsman_id: str) -> Optional[entities.craftsman.Craftsman]:
        for craftsman in self.current_state.craftsmen:
            if craftsman.id == craftsman_id:
                return craftsman
        return None

    def _agent_name_to_craftsman(self, agent: str) -> Optional[entities.craftsman.Craftsman]:
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
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.STAY))
        elif command == 1:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE,
                                                                 direction=Direction.UP))
        elif command == 2:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE,
                                                                 direction=Direction.DOWN))
        elif command == 3:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE,
                                                                 direction=Direction.LEFT))
        elif command == 4:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE,
                                                                 direction=Direction.RIGHT))
        elif command == 5:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE
                                                                 , direction=Direction.UP_LEFT))
        elif command == 6:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE
                                                                 , direction=Direction.UP_RIGHT))
        elif command == 7:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE
                                                                 , direction=Direction.DOWN_LEFT))
        elif command == 8:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE
                                                                 , direction=Direction.DOWN_RIGHT))
        elif command == 9:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.BUILD,
                                                                 direction=Direction.UP))
        elif command == 10:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.BUILD,
                                                                 direction=Direction.DOWN))
        elif command == 11:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.BUILD,
                                                                 direction=Direction.LEFT))
        elif command == 12:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.BUILD,
                                                                 direction=Direction.RIGHT))
        elif command == 13:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY
                                                                 , direction=Direction.UP))
        elif command == 14:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY
                                                                 , direction=Direction.DOWN))
        elif command == 15:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY
                                                                 , direction=Direction.LEFT))
        elif command == 16:
            self.add_command(entities.craftsman.CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY
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
                arr[y][x][6] = tile.t1c
                arr[y][x][7] = tile.t2c
                arr[y][x][8] = tile.t1o
                arr[y][x][9] = tile.t2o
                arr[y][x][10] = self.current_state.turn_state == TurnState.TEAM2_TURN
                arr[y][x][11] = (x, y) in craftman_tcur_action_committed

        return arr.flatten()

    def process_turn(self):
        if self.is_game_over:
            return
        commands = self.categorize_and_deduplicate_commands_from_buffer()
        self.command_buffer.clear()

        command_res = []

        prev_turn_state = deepcopy(self.current_state)
        phase_start_state = deepcopy(self.current_state)
        self.history.append({
            "score": self.score,
            "state": prev_turn_state
        })

        for command in commands["destroy"]:
            selected = entities.craftsman.get_craftsman_at(phase_start_state.craftsmen, command.craftsman_pos)
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
            selected = entities.craftsman.get_craftsman_at(phase_start_state.craftsmen, command.craftsman_pos)
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
            selected = entities.craftsman.get_craftsman_at(phase_start_state.craftsmen, command.craftsman_pos)
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
        territory_computed_map = score_compute.get_territory_computed_map(prev_turn_state.map, self.current_state.map)
        self.current_state.map = territory_computed_map

        self.current_state.turn_number += 1
        self.current_state.turn_state = TurnState.TEAM2_TURN if self.current_state.turn_number % 2 == 0 else TurnState.TEAM1_TURN

        # set has_commited_action to False for all craftsmen
        for craftsman in self.current_state.craftsmen:
            craftsman.has_committed_action = False

        if self.is_game_over:
            self.current_state.turn_state = TurnState.GAME_OVER
            self.history.append({
                "score": self.score,
                "winner": self.winning_team,
                "state": self.current_state
            })

            print("Writing history to file...")
            thread = threading.Thread(target=save_game_history, args=(self.history,))
            thread.start()

        return command_res

    @property
    def score(self) -> dict:
        return score_compute.compute_score(self.current_state.map, self.score_coefficients)

    @property
    def winning_team(self) -> Team:
        score = self.score
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
        self.history.clear()
        self.command_buffer.clear()
        self.score_coefficients = ScoreCoefficients(1, 1, 1)
        self.max_turn = 100


def can_select_piece(piece_team: Team, turn_state: TurnState):
    return (piece_team == Team.TEAM1 and turn_state == TurnState.TEAM1_TURN) or \
        (piece_team == Team.TEAM2 and turn_state == TurnState.TEAM2_TURN)
