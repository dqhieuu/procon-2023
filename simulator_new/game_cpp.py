from bin.game_interfaces_binding import Game, GameState, GameAction, GameOptions, ActionType, SubActionType, TileMask, Craftsman, MapState
from utils import get_direction_vector

from utils_cpp import load_offline_game, load_offline_actions, calculate_score, server_action_to_cpp_action
from fastapi import FastAPI, HTTPException
from fastapi_restful.tasks import repeat_every
from model import Direction, CraftsmanCommand, PyActionType
import aiohttp

action_path = "test-cases/match-249.txt"
map_path = "test-cases/map-249-game-2.txt"

# GameOptions(), Map(), list[Craftsman]
game_options, map, craftsmen, craftsman_strid_to_intid_map = load_offline_game(
    map_path)

online_room = -1

command_buffer_t1: dict[int, CraftsmanCommand] = {}
command_buffer_t2: dict[int, CraftsmanCommand] = {}

command_order_t1: dict[int, int] = {}
command_order_t2: dict[int, int] = {}

command_counter = 0

actions_by_turn = load_offline_actions(
    action_path, craftsman_strid_to_intid_map)

game = Game(game_options, map, craftsmen)

# for actions in actions_by_turn:
#     for action in actions:
#         game.addAction(action)
#     game.nextTurn()

app = FastAPI()
session = aiohttp.ClientSession()


@app.post("/command")
async def do_command(command: CraftsmanCommand):
    global command_counter

    if online_room > 0:
        pass
    else:
        # LOCAL MODE
        current_state = game.getCurrentState()
        craftsman_id = current_state.findCraftsmanIdByPos(
            *command.craftsman_pos)
        craftsman_is_t1 = current_state.craftsmen[craftsman_id].isT1

        selected_buffer = command_buffer_t1 if craftsman_is_t1 else command_buffer_t2
        selected_order = command_order_t1 if craftsman_is_t1 else command_order_t2

        if (craftsman_id == -1):
            raise HTTPException(status_code=400, detail="Craftsman not found")

        selected_buffer[craftsman_id] = command
        selected_order[craftsman_id] = command_counter

        command_counter += 1

        return "OK"


@app.post("/end_turn")
async def end_turn():
    if online_room > 0:
        # ONLINE MODE, noop
        return "OK"
    else:
        # LOCAL MODE
        is_t1_turn = game.getCurrentState().isT1Turn

        selected_buffer = command_buffer_t1 if is_t1_turn else command_buffer_t2
        selected_order = command_order_t1 if is_t1_turn else command_order_t2

        command_list_with_craftsman_id = sorted(
            selected_buffer.items(),
            key=lambda craftsman_id, command: selected_order[craftsman_id]
        )

        for craftsman_id, command in command_list_with_craftsman_id:
            if command.action_type == PyActionType.STAY:
                continue

            action, subaction = server_action_to_cpp_action(
                command.action_type, command.direction)

            game.addAction(GameAction(
                craftsman_id,
                action,
                subaction
            ))

        game.nextTurn()

        selected_buffer.clear()

        return "OK"


@app.get("/current_state")
async def current_state():
    game_state = game.getCurrentState()

    map_state = game_state.map.tiles

    craftsmen = []

    for craftsman in game_state.craftsmen.values():
        craftsmen.append({
            "team": "team1" if craftsman.isT1 else "team2",
            "pos": (craftsman.x, craftsman.y)
        })

    res = {
        "score": calculate_score(map_state, game_options),
        "state": {
            "turn_number": game_state.turn,
            "turn_state": "team1_turn" if game_state.isT1Turn else "team2_turn",
            "map": map_state,
            "craftsmen": craftsmen,
        },
        "options": {
            "map_width": game.gameOptions.mapWidth,
            "map_height": game.gameOptions.mapHeight,
        }
    }

    command_list_with_craftsman_id = [
        *command_buffer_t1.items(),
        *command_buffer_t2.items()
    ]

    actions_to_be_applied = []
    for craftsman_id, command in command_list_with_craftsman_id:
        if command.direction is None:
            continue
        craftsman = game_state.craftsmen[craftsman_id]
        dir_vec = get_direction_vector(command.direction)

        actions_to_be_applied.append({
            'pos': (craftsman.x + dir_vec[0], craftsman.y + dir_vec[1]),
            'action_type': command.action_type,
        })

    res['actions_to_be_applied'] = actions_to_be_applied

    return res
