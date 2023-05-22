from copy import deepcopy

from objprint import op

from entities.craftman import CraftmanCommand, get_craftman_at, Craftman
from entities.game_state import GameState
from entities.tile import Tile
from entities.utils.enums import ActionType, get_direction_vector, Team, TurnState


class Game:
    def __init__(self, map_path: str):
        self.current_state = GameState()
        self.history: list[GameState] = [self.current_state]
        self.command_buffer: list[CraftmanCommand] = []

        self.load_map(map_path)

    def categorize_and_deduplicate_commands_from_buffer(self):
        craftman_pos_dict = {}
        result: dict[str, list[CraftmanCommand]] = {
            "move": [],
            "build": [],
            "destroy": []
        }
        for command in self.command_buffer:
            craftman_pos_dict[command.craftman_pos] = command
        for command in craftman_pos_dict.values():
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
                if line == "map" or line == "team1" or line == "team2":
                    mode = line
                    continue

                if mode == "map":
                    self.current_state.map.map.append([Tile.from_file_string(tile) for tile in list(line)])
                elif mode == "team1" or mode == "team2":
                    pos = list(map(int, line.split(" ")))
                    self.current_state.craftmen.append(
                        Craftman(Team.TEAM1 if mode == "team1" else Team.TEAM2, (pos[0], pos[1])))

    def add_command(self, command: CraftmanCommand):
        self.command_buffer.append(command)

    def process_turn(self):
        commands = self.categorize_and_deduplicate_commands_from_buffer()
        self.command_buffer.clear()

        command_res = []

        phase_start_state = deepcopy(self.current_state)
        self.history.append(phase_start_state)

        for command in commands["destroy"]:
            selected = get_craftman_at(phase_start_state.craftmen, command.craftman_pos)
            if selected is not None:
                if can_select_piece(selected.team, phase_start_state.turn_state) is False:
                    command_res.append("Cannot select enemy craftman (at {})".format(command.craftman_pos))
                    continue
                selected = selected.with_game_state(phase_start_state, self.current_state)
                res = selected.destroy(get_direction_vector(command.direction))
                command_res.append(res)
                if res.success:
                    self.current_state = res.game_state_after

        phase_start_state = deepcopy(self.current_state)
        for command in commands["build"]:
            selected = get_craftman_at(phase_start_state.craftmen, command.craftman_pos)
            if selected is not None:
                if can_select_piece(selected.team, phase_start_state.turn_state) is False:
                    command_res.append("Cannot select enemy craftman (at {})".format(command.craftman_pos))
                    continue
                selected = selected.with_game_state(phase_start_state, self.current_state)
                res = selected.build(get_direction_vector(command.direction))
                command_res.append(res)
                if res.success:
                    self.current_state = res.game_state_after

        phase_start_state = deepcopy(self.current_state)
        for command in commands["move"]:
            selected = get_craftman_at(phase_start_state.craftmen, command.craftman_pos)
            if selected is not None:
                if can_select_piece(selected.team, phase_start_state.turn_state) is False:
                    command_res.append("Cannot select enemy craftman (at {})".format(command.craftman_pos))
                    continue
                selected = selected.with_game_state(phase_start_state, self.current_state)
                res = selected.move(get_direction_vector(command.direction))
                command_res.append(res)
                if res.success:
                    self.current_state = res.game_state_after

        self.current_state.turn_number += 1
        self.current_state.turn_state = TurnState.TEAM1_TURN if self.current_state.turn_state == TurnState.TEAM2_TURN else TurnState.TEAM2_TURN
        return command_res

    def __reset_game_state(self):
        self.current_state = GameState()
        self.history = [self.current_state]
        self.command_buffer = []


def can_select_piece(piece_team: Team, turn_state: TurnState):
    return (piece_team == Team.TEAM1 and turn_state == TurnState.TEAM1_TURN) or \
        (piece_team == Team.TEAM2 and turn_state == TurnState.TEAM2_TURN)
# if __name__ == "__main__":
#     game = Game("assets/map1.txt")
#     op(game)
