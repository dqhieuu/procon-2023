from bin.game_interfaces_binding import Game, GameState, GameAction, GameOptions, ActionType, SubActionType, TileMask, Craftsman, MapState

from utils_cpp import load_map

# GameOptions(), Map(), list[Craftsman]
game_options, map, craftsmen = load_game(map_path)


action_data: list[GameAction] = load_action(action_path)

def load_game() -> (GameOptions, list[list[int]], list[Craftsman]):



game = Game(game_options, map, craftsmen)