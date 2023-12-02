from bin.game_interfaces_binding import ActionType, Craftsman, GameAction, GameOptions, SubActionType, TileMask

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


def idx_to_action_enum(idx: int):
    return idx_to_action_enum_list[idx]


def load_offline_game(path: str) -> tuple[GameOptions, list[list[int]], list[Craftsman], dict[str, int]]:
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

    go = GameOptions()
    go.mapWidth = map_data['game_settings']['map_width']
    go.mapHeight = map_data['game_settings']['map_height']
    go.maxTurns = map_data['game_settings']['max_turn']
    go.wallCoeff = map_data['score_coefficients']['wall']
    go.castleCoeff = map_data['score_coefficients']['castle']
    go.territoryCoeff = map_data['score_coefficients']['territory']

    return go, map_formatted, craftsmen_formatted, craftsman_strid_to_intid


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
