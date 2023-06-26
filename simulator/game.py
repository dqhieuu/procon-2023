from copy import deepcopy

from entities.craftsman import CraftsmanCommand, get_craftsman_at, Craftsman
from entities.game_map import ScoreCoefficients
from entities.game_state import GameState
from entities.tile import Tile
from entities.utils.enums import ActionType, get_direction_vector, Team, TurnState
from score_compute import get_territory_computed_map, compute_score


class Game:
    def __init__(self, map_path: str):
        self.current_state = GameState()
        self.history: list[GameState] = [self.current_state]
        self.command_buffer: list[CraftsmanCommand] = []

        self.score_coefficients = ScoreCoefficients(territory=1, wall=1, castle=1)

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
        with open(file_path, "r") as f:
            self.__reset_game_state()
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

                if mode == "map":
                    self.current_state.map.map.append([Tile.from_file_string(tile) for tile in list(line)])
                elif mode == "team1" or mode == "team2":
                    pos = list(map(int, line.split(" ")))
                    self.current_state.craftsmen.append(
                        Craftsman(Team.TEAM1 if mode == "team1" else Team.TEAM2, (pos[0], pos[1])))
            # flips map so that (0,0) means bottom left corner
            # self.current_state.map.map = list(reversed(self.current_state.map.map))

    def add_command(self, command: CraftsmanCommand):
        self.command_buffer.append(command)

    def process_turn(self):
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
            print(command.craftsman_pos,phase_start_state.craftsmen,get_craftsman_at(phase_start_state.craftsmen, command.craftsman_pos))
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
        return command_res

    @property
    def score(self):
        return compute_score(self.current_state.map, self.score_coefficients)
    def __reset_game_state(self):
        self.current_state = GameState()
        self.history = [self.current_state]
        self.command_buffer = []


def can_select_piece(piece_team: Team, turn_state: TurnState):
    return (piece_team == Team.TEAM1 and turn_state == TurnState.TEAM1_TURN) or \
        (piece_team == Team.TEAM2 and turn_state == TurnState.TEAM2_TURN)