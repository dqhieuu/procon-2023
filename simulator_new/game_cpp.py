from bin.game_interfaces_binding import Game, GameState, GameAction, GameOptions, ActionType, SubActionType, TileMask, Craftsman, MapState

from utils_cpp import load_offline_game, load_offline_actions, calculate_score
from fastapi import FastAPI, HTTPException
from fastapi_restful.tasks import repeat_every
from model import Direction, CraftsmanCommand, ActionTypeServer
import aiohttp

action_path = "test-cases/match-249.txt"
map_path = "test-cases/map-249-game-2.txt"

# GameOptions(), Map(), list[Craftsman]
game_options, map, craftsmen, craftsman_strid_to_intid_map = load_offline_game(map_path)

online_room = 0

command_buffer_t1: dict[int, CraftsmanCommand] = {}
command_buffer_t2: dict[int, CraftsmanCommand] = {}

command_order_t1: dict[int, int] = {}
command_order_t2: dict[int, int] = {}

command_counter = 0

actions_by_turn = load_offline_actions(action_path, craftsman_strid_to_intid_map)

game = Game(game_options, map, craftsmen)

# for actions in actions_by_turn:
#     for action in actions:
#         game.addAction(action)
#     game.nextTurn()

app = FastAPI()
session = aiohttp.ClientSession()

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

@app.post("/command")
async def do_command(command: CraftsmanCommand):
    global command_counter

    if online_room > 0:
        pass
    else:
        # LOCAL MODE
        current_state = game.getCurrentState()
        craftsman_id = current_state.findCraftsmanIdByPos(*command.craftsman_pos)
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
        
        command_list_with_craftsman_id = sorted(selected_buffer.items(), key=lambda id_and_command: selected_order[id_and_command[0]])

        for craftsman_id, command in command_list_with_craftsman_id:
            if command.action_type == ActionTypeServer.STAY:
                continue
            
            if command.action_type == ActionTypeServer.MOVE:
                if command.direction is Direction.UP:
                    subaction, action = SubActionType.MOVE_UP, ActionType.MOVE
                elif command.direction is Direction.DOWN:
                    subaction, action = SubActionType.MOVE_DOWN, ActionType.MOVE
                elif command.direction is Direction.LEFT:
                    subaction, action = SubActionType.MOVE_LEFT, ActionType.MOVE
                elif command.direction is Direction.RIGHT:
                    subaction, action = SubActionType.MOVE_RIGHT, ActionType.MOVE
                elif command.direction is Direction.UP_LEFT:
                    subaction, action = SubActionType.MOVE_UP_LEFT, ActionType.MOVE
                elif command.direction is Direction.UP_RIGHT:
                    subaction, action = SubActionType.MOVE_UP_RIGHT, ActionType.MOVE
                elif command.direction is Direction.DOWN_LEFT:
                    subaction, action = SubActionType.MOVE_DOWN_LEFT, ActionType.MOVE
                elif command.direction is Direction.DOWN_RIGHT:
                    subaction, action = SubActionType.MOVE_DOWN_RIGHT, ActionType.MOVE
            elif command.action_type == ActionTypeServer.BUILD:
                if command.direction is Direction.UP:
                    subaction, action = SubActionType.BUILD_UP, ActionType.BUILD
                elif command.direction is Direction.DOWN:
                    subaction, action = SubActionType.BUILD_DOWN, ActionType.BUILD
                elif command.direction is Direction.LEFT:
                    subaction, action = SubActionType.BUILD_LEFT, ActionType.BUILD
                elif command.direction is Direction.RIGHT:
                    subaction, action = SubActionType.BUILD_RIGHT, ActionType.BUILD
            elif command.action_type == ActionTypeServer.DESTROY:
                if command.direction is Direction.UP:
                    subaction, action = SubActionType.DESTROY_UP, ActionType.DESTROY
                elif command.direction is Direction.DOWN:
                    subaction, action = SubActionType.DESTROY_DOWN, ActionType.DESTROY
                elif command.direction is Direction.LEFT:
                    subaction, action = SubActionType.DESTROY_LEFT, ActionType.DESTROY
                elif command.direction is Direction.RIGHT:
                    subaction, action = SubActionType.DESTROY_RIGHT, ActionType.DESTROY

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
    current_game_state = game.getCurrentState()

    map_state = current_game_state.map.tiles

    craftsmen = []

    for idx, craftsman in current_game_state.craftsmen.items():
        craftsmen.append({
            "team": "team1" if craftsman.isT1 else "team2",
            "pos": (craftsman.x, craftsman.y)
        })


    res = {
        "score": calculate_score(map_state, game_options),
        "state": {
            "turn_number": current_game_state.turn,
            # "team1_turn" if current_game_state.isT1Turn#
            "turn_state": "team1_turn" if current_game_state.isT1Turn else "team2_turn",
            "map": map_state,
            "craftsmen": craftsmen,
        },
    }

    command_list_with_craftsman_id = [*command_buffer_t1.items(),*command_buffer_t2.items()]

    actions_to_be_applied = []
    for craftsman_id, command in command_list_with_craftsman_id:
        if command.direction is None:
            continue
        craftsman = current_game_state.craftsmen[craftsman_id]
        dir_vec = get_direction_vector(command.direction)

        actions_to_be_applied.append({
            'pos': (craftsman.x + dir_vec[0], craftsman.y + dir_vec[1]),
            'action_type': command.action_type,
        })
    
    res['actions_to_be_applied'] = actions_to_be_applied

    return res