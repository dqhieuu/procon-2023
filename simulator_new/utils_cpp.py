from bin.game_interfaces_binding import Game, GameState, GameAction, GameOptions, ActionType, SubActionType, TileMask, Craftsman, MapState
from model import Direction, PyActionType
from copy import deepcopy
from functools import wraps
import time
from typing import List


def load_map(file_path):
    score_coefficients = {
        "territory": 0,
        "wall": 0,
        "castle": 0
    }
    game_settings = {
        "max_turn": 0,
        "map_width": 0,
        "map_height": 0
    }

    game_map = []

    craftsmen = {
        "team1": [],
        "team2": []
    }

    with open(file_path, "r") as f:
        mode = ""
        for line in f:
            line = line.strip()
            if line == "":
                continue
            elif line == "map" or line == "team1" or line == "team2":
                mode = line
                continue
            elif line.startswith("territory"):
                mode = ""
                score_coefficients["territory"] = int(line.split(" ")[1])
            elif line.startswith("wall"):
                mode = ""
                score_coefficients["wall"] = int(line.split(" ")[1])
            elif line.startswith("castle"):
                mode = ""
                score_coefficients["castle"] = int(line.split(" ")[1])
            elif line.startswith("turns"):
                mode = ""
                game_settings["max_turn"] = int(line.split(" ")[1])

            if mode == "map":
                game_map.append(list(map(int, list(line))))
            elif mode == "team1" or mode == "team2":
                data = line.split(" ")
                craftsmen[mode].append(
                    {"x": int(data[1]), "y": int(data[2]), "id": data[0]})

    game_settings["map_width"] = len(game_map[0])
    game_settings["map_height"] = len(game_map)

    return {
        "game_map": game_map,
        "score_coefficients": score_coefficients,
        "game_settings": game_settings,
        "craftsmen": craftsmen,
    }


def map_tile_to_bitmask(tile):
    if tile == 1:
        return 1 << TileMask.POND.value
    elif tile == 2:
        return 1 << TileMask.CASTLE.value
    return 0


idx_to_action_enum_list = [
    (ActionType.MOVE, SubActionType.MOVE_UP),
    (ActionType.MOVE, SubActionType.MOVE_DOWN),
    (ActionType.MOVE, SubActionType.MOVE_LEFT),
    (ActionType.MOVE, SubActionType.MOVE_RIGHT),
    (ActionType.MOVE, SubActionType.MOVE_UP_LEFT),
    (ActionType.MOVE, SubActionType.MOVE_UP_RIGHT),
    (ActionType.MOVE, SubActionType.MOVE_DOWN_LEFT),
    (ActionType.MOVE, SubActionType.MOVE_DOWN_RIGHT),
    (ActionType.BUILD, SubActionType.BUILD_UP),
    (ActionType.BUILD, SubActionType.BUILD_DOWN),
    (ActionType.BUILD, SubActionType.BUILD_LEFT),
    (ActionType.BUILD, SubActionType.BUILD_RIGHT),
    (ActionType.DESTROY, SubActionType.DESTROY_UP),
    (ActionType.DESTROY, SubActionType.DESTROY_DOWN),
    (ActionType.DESTROY, SubActionType.DESTROY_LEFT),
    (ActionType.DESTROY, SubActionType.DESTROY_RIGHT),
    (ActionType.STAY, SubActionType.STAY),
]


def idx_to_action_enum(idx):
    return idx_to_action_enum_list[idx]


def load_offline_game(path: str) -> tuple[GameOptions, list[list[int]], list[Craftsman], dict[str, int], dict[int, str]]:
    map_data = load_map(path)
    map_formatted = [[map_tile_to_bitmask(x) for x in row]
                     for row in map_data['game_map']]

    counter = 0
    craftsman_strid_to_intid: dict[str, int] = {}
    craftsmen_formatted: list[Craftsman] = []
    for c in map_data['craftsmen']['team1']:
        new_craftsman = Craftsman(counter, c['x'], c['y'], True)
        craftsmen_formatted.append(new_craftsman)
        craftsman_strid_to_intid[c['id']] = counter
        counter += 1
    for c in map_data['craftsmen']['team2']:
        new_craftsman = Craftsman(counter, c['x'], c['y'], False)
        craftsmen_formatted.append(new_craftsman)
        craftsman_strid_to_intid[c['id']] = counter
        counter += 1

    craftsman_intid_to_strid = {v: k for k, v in craftsman_strid_to_intid.items()}

    go = GameOptions()
    go.mapWidth = map_data['game_settings']['map_width']
    go.mapHeight = map_data['game_settings']['map_height']
    go.maxTurns = map_data['game_settings']['max_turn']
    go.wallCoeff = map_data['score_coefficients']['wall']
    go.castleCoeff = map_data['score_coefficients']['castle']
    go.territoryCoeff = map_data['score_coefficients']['territory']

    return go, map_formatted, craftsmen_formatted, craftsman_strid_to_intid, craftsman_intid_to_strid


def load_offline_actions(path: str, craftsman_strid_to_intid_map: dict) -> list[list[GameAction]]:
    actiontxt = open(path, "r").read()

    # Split the input string based on "- -"
    turns = actiontxt.strip().split("- -")

    # Remove empty strings from the list
    turns = [section.strip() for section in turns]

    # Convert each section to an array of arrays
    actions = []
    for turn in turns:
        if not turn:
            actions.append([])
            continue

        turn_actions = []
        for action in turn.split('\n'):
            turn_actions.append(action.split(' '))

        actions.append(turn_actions)

    actions_temp = []

    for turn in actions:
        turn_actions = []
        for craftsman_str_id, action_idx in turn:
            game_action = GameAction(
                craftsman_strid_to_intid_map[craftsman_str_id], *idx_to_action_enum(int(action_idx)))
            turn_actions.append(game_action)
        actions_temp.append(turn_actions)

    actions = actions_temp

    return actions


def calculate_score(state: list[list[int]], game_options: GameOptions):
    width = game_options.mapWidth
    height = game_options.mapHeight

    res = {
        "team1": {
            "count": {
                "territory": 0,
                "close": 0,
                "open": 0,
                "wall": 0,
                "castle": 0
            },
            "points": {
                "territory": 0,
                "close": 0,
                "open": 0,
                "wall": 0,
                "castle": 0,
                "total": 0
            }
        },
        "team2": {
            "count": {
                "territory": 0,
                "close": 0,
                "open": 0,
                "wall": 0,
                "castle": 0
            },
            "points": {
                "territory": 0,
                "close": 0,
                "open": 0,
                "wall": 0,
                "castle": 0,
                "total": 0
            }
        }
    }

    for row in range(height):
        for col in range(width):
            if state[row][col] & 1 << TileMask.T1_CLOSE_TERRITORY.value or state[row][col] & 1 << TileMask.T1_OPEN_TERRITORY.value:
                if state[row][col] & 1 << TileMask.T1_CLOSE_TERRITORY.value:
                    res["team1"]["count"]["close"] += 1
                    res["team1"]["points"]["close"] += game_options.territoryCoeff
                else:
                    res["team1"]["count"]["open"] += 1
                    res["team1"]["points"]["open"] += game_options.territoryCoeff
                if state[row][col] & 1 << TileMask.CASTLE.value:
                    res["team1"]["count"]["castle"] += 1
                    res["team1"]["points"]["castle"] += game_options.castleCoeff
            elif state[row][col] & 1 << TileMask.T2_CLOSE_TERRITORY.value or state[row][col] & 1 << TileMask.T2_OPEN_TERRITORY.value:
                if state[row][col] & 1 << TileMask.T2_CLOSE_TERRITORY.value:
                    res["team2"]["count"]["close"] += 1
                    res["team2"]["points"]["close"] += game_options.territoryCoeff
                else:
                    res["team2"]["count"]["open"] += 1
                    res["team2"]["points"]["open"] += game_options.territoryCoeff
                if state[row][col] & 1 << TileMask.CASTLE.value:
                    res["team2"]["count"]["castle"] += 1
                    res["team2"]["points"]["castle"] += game_options.castleCoeff
            elif state[row][col] & 1 << TileMask.T1_WALL.value:
                res["team1"]["count"]["wall"] += 1
                res["team1"]["points"]["wall"] += game_options.wallCoeff
            elif state[row][col] & 1 << TileMask.T2_WALL.value:
                res["team2"]["count"]["wall"] += 1
                res["team2"]["points"]["wall"] += game_options.wallCoeff

    res["team1"]["count"]["territory"] = res["team1"]["count"]["close"] + \
        res["team1"]["count"]["open"]
    res["team2"]["count"]["territory"] = res["team2"]["count"]["close"] + \
        res["team2"]["count"]["open"]

    res["team1"]["points"]["territory"] = res["team1"]["points"]["close"] + \
        res["team1"]["points"]["open"]
    res["team2"]["points"]["territory"] = res["team2"]["points"]["close"] + \
        res["team2"]["points"]["open"]

    res["team1"]["points"]["total"] = res["team1"]["points"]["territory"] + \
        res["team1"]["points"]["wall"] + res["team1"]["points"]["castle"]
    res["team2"]["points"]["total"] = res["team2"]["points"]["territory"] + \
        res["team2"]["points"]["wall"] + res["team2"]["points"]["castle"]

    return res


def local_action_to_cpp_action(action_type: PyActionType, direction: Direction) -> tuple[ActionType, SubActionType]:
    if action_type == PyActionType.STAY:
        return ActionType.STAY, SubActionType.STAY
    elif action_type == PyActionType.MOVE:
        if direction is Direction.UP:
            return ActionType.MOVE, SubActionType.MOVE_UP
        elif direction is Direction.DOWN:
            return ActionType.MOVE, SubActionType.MOVE_DOWN
        elif direction is Direction.LEFT:
            return ActionType.MOVE, SubActionType.MOVE_LEFT
        elif direction is Direction.RIGHT:
            return ActionType.MOVE, SubActionType.MOVE_RIGHT
        elif direction is Direction.UP_LEFT:
            return ActionType.MOVE, SubActionType.MOVE_UP_LEFT
        elif direction is Direction.UP_RIGHT:
            return ActionType.MOVE, SubActionType.MOVE_UP_RIGHT
        elif direction is Direction.DOWN_LEFT:
            return ActionType.MOVE, SubActionType.MOVE_DOWN_LEFT
        elif direction is Direction.DOWN_RIGHT:
            return ActionType.MOVE, SubActionType.MOVE_DOWN_RIGHT
    elif action_type == PyActionType.BUILD:
        if direction is Direction.UP:
            return ActionType.BUILD, SubActionType.BUILD_UP
        elif direction is Direction.DOWN:
            return ActionType.BUILD, SubActionType.BUILD_DOWN
        elif direction is Direction.LEFT:
            return ActionType.BUILD, SubActionType.BUILD_LEFT
        elif direction is Direction.RIGHT:
            return ActionType.BUILD, SubActionType.BUILD_RIGHT
    elif action_type == PyActionType.DESTROY:
        if direction is Direction.UP:
            return ActionType.DESTROY, SubActionType.DESTROY_UP
        elif direction is Direction.DOWN:
            return ActionType.DESTROY, SubActionType.DESTROY_DOWN
        elif direction is Direction.LEFT:
            return ActionType.DESTROY, SubActionType.DESTROY_LEFT
        elif direction is Direction.RIGHT:
            return ActionType.DESTROY, SubActionType.DESTROY_RIGHT

def cpp_action_to_local_action(action_type: ActionType, sub_action_type: SubActionType) -> tuple[PyActionType, Direction]:
    if action_type == ActionType.STAY:
        return PyActionType.STAY, Direction.STAY
    elif action_type == ActionType.MOVE:
        if sub_action_type == SubActionType.MOVE_UP:
            return PyActionType.MOVE, Direction.UP
        elif sub_action_type == SubActionType.MOVE_DOWN:
            return PyActionType.MOVE, Direction.DOWN
        elif sub_action_type == SubActionType.MOVE_LEFT:
            return PyActionType.MOVE, Direction.LEFT
        elif sub_action_type == SubActionType.MOVE_RIGHT:
            return PyActionType.MOVE, Direction.RIGHT
        elif sub_action_type == SubActionType.MOVE_UP_LEFT:
            return PyActionType.MOVE, Direction.UP_LEFT
        elif sub_action_type == SubActionType.MOVE_UP_RIGHT:
            return PyActionType.MOVE, Direction.UP_RIGHT
        elif sub_action_type == SubActionType.MOVE_DOWN_LEFT:
            return PyActionType.MOVE, Direction.DOWN_LEFT
        elif sub_action_type == SubActionType.MOVE_DOWN_RIGHT:
            return PyActionType.MOVE, Direction.DOWN_RIGHT
    elif action_type == ActionType.BUILD:
        if sub_action_type == SubActionType.BUILD_UP:
            return PyActionType.BUILD, Direction.UP
        elif sub_action_type == SubActionType.BUILD_DOWN:
            return PyActionType.BUILD, Direction.DOWN
        elif sub_action_type == SubActionType.BUILD_LEFT:
            return PyActionType.BUILD, Direction.LEFT
        elif sub_action_type == SubActionType.BUILD_RIGHT:
            return PyActionType.BUILD, Direction.RIGHT
    elif action_type == ActionType.DESTROY:
        if sub_action_type == SubActionType.DESTROY_UP:
            return PyActionType.DESTROY, Direction.UP
        elif sub_action_type == SubActionType.DESTROY_DOWN:
            return PyActionType.DESTROY, Direction.DOWN
        elif sub_action_type == SubActionType.DESTROY_LEFT:
            return PyActionType.DESTROY, Direction.LEFT
        elif sub_action_type == SubActionType.DESTROY_RIGHT:
            return PyActionType.DESTROY, Direction.RIGHT

def online_action_to_cpp_action(action_type: str, action_param: str) -> tuple[ActionType, SubActionType]:
    if action_type == "STAY":
        return ActionType.STAY, SubActionType.STAY
    elif action_type == "MOVE":
        if action_param == "UP":
            return ActionType.MOVE, SubActionType.MOVE_UP
        elif action_param == "DOWN":
            return ActionType.MOVE, SubActionType.MOVE_DOWN
        elif action_param == "LEFT":
            return ActionType.MOVE, SubActionType.MOVE_LEFT
        elif action_param == "RIGHT":
            return ActionType.MOVE, SubActionType.MOVE_RIGHT
        elif action_param == "UPPER_LEFT":
            return ActionType.MOVE, SubActionType.MOVE_UP_LEFT
        elif action_param == "UPPER_RIGHT":
            return ActionType.MOVE, SubActionType.MOVE_UP_RIGHT
        elif action_param == "LOWER_LEFT":
            return ActionType.MOVE, SubActionType.MOVE_DOWN_LEFT
        elif action_param == "LOWER_RIGHT":
            return ActionType.MOVE, SubActionType.MOVE_DOWN_RIGHT
    elif action_type == "BUILD":
        if action_param == "ABOVE":
            return ActionType.BUILD, SubActionType.BUILD_UP
        elif action_param == "BELOW":
            return ActionType.BUILD, SubActionType.BUILD_DOWN
        elif action_param == "LEFT":
            return ActionType.BUILD, SubActionType.BUILD_LEFT
        elif action_param == "RIGHT":
            return ActionType.BUILD, SubActionType.BUILD_RIGHT
    elif action_type == "DESTROY":
        if action_param == "ABOVE":
            return ActionType.DESTROY, SubActionType.DESTROY_UP
        elif action_param == "BELOW":
            return ActionType.DESTROY, SubActionType.DESTROY_DOWN
        elif action_param == "LEFT":
            return ActionType.DESTROY, SubActionType.DESTROY_LEFT
        elif action_param == "RIGHT":
            return ActionType.DESTROY, SubActionType.DESTROY_RIGHT


def get_direction_vector(direction: Direction) -> tuple[int, int]:
    if direction == Direction.UP:
        return 0, -1
    elif direction == Direction.DOWN:
        return 0, 1
    elif direction == Direction.LEFT:
        return -1, 0
    elif direction == Direction.RIGHT:
        return 1, 0
    elif direction == Direction.UP_LEFT:
        return -1, -1
    elif direction == Direction.UP_RIGHT:
        return 1, -1
    elif direction == Direction.DOWN_LEFT:
        return -1, 1
    elif direction == Direction.DOWN_RIGHT:
        return 1, 1


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(
            f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result

    return timeit_wrapper