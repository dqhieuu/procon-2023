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
                pos = list(map(int, line.split(" ")))
                craftsmen[mode].append(pos)

    game_settings["map_width"] = len(game_map[0])
    game_settings["map_height"] = len(game_map)

    return {
        "game_map": game_map,
        "score_coefficients": score_coefficients,
        "game_settings": game_settings,
        "craftsmen": craftsmen,
    }
