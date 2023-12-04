from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import json
import math
import re
from typing import Any, Union
from pydantic import BaseModel
import requests
from bin.game_interfaces_binding import Game, GameAction, TileMask
from online import OnlineActionResponseList, OnlineGameStatus, OnlineFieldRequestList, load_online_actions, load_online_game, local_command_to_online_action, online_field_decoder
from utils_cpp import cpp_action_to_local_action, load_offline_game, load_offline_actions, calculate_score, local_action_to_cpp_action, get_direction_vector
from fastapi import FastAPI, HTTPException
from fastapi_restful.tasks import repeat_every
from model import CraftsmanCommand, PyActionType
import aiohttp


### SET THESE VARIABLES ###
BASE_URL = "https://procon2023.duckdns.org/api"

competition_token = None
team_1_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NTUsIm5hbWUiOiJ1ZXQxIiwiaXNfYWRtaW4iOmZhbHNlLCJpYXQiOjE3MDE2ODU0NzksImV4cCI6MTcwMTg1ODI3OX0.BkhNAy55QI2-MV4ku-7m09TaK1ASBxJnaz3M1KBTqOU"
team_2_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NTYsIm5hbWUiOiJ1ZXQyIiwiaXNfYWRtaW4iOmZhbHNlLCJpYXQiOjE3MDE2ODU1MDUsImV4cCI6MTcwMTg1ODMwNX0.KJSgUIaWtuvz-vyrQkFh-xH10qI8q4TAvHoUuQDvoJQ"

action_path = "test-cases/match-249.txt"
map_path = "test-cases/map-249-game-2.txt"
### END SET THESE VARIABLES ###

global_token: Union[str, None] = None
online_room = -1

time_per_turn = None
start_time = None
max_turn = None
client_delay = 0

command_counter = 0

command_buffer_t1: dict[int, CraftsmanCommand] = {}
command_buffer_t2: dict[int, CraftsmanCommand] = {}
online_command_buffer_t1: dict[int, dict[str, Any]] = {}
online_command_buffer_t2: dict[int, dict[str, Any]] = {}

command_order_t1: dict[int, int] = {}
command_order_t2: dict[int, int] = {}
builder_pos_by_craftsman: dict[str, list[tuple[int, int]]] = {}

mode = 0


def load_cli():
    global global_token, online_room, team_1_token, team_2_token, competition_token, mode

    print("""SELECT A MODE:
1. Local
2. Online, practice: team A - team B
3. Online, practice: swap team A - team B token
4. Online, competition: you = team A
5. Online, competition: you = team B""")

    while True:
        mode = input()
        if not (mode.isdigit() and 1 <= int(mode) <= 5):
            print(f"Invalid mode")
        else:
            mode = int(mode)
            break

    if 2 <= mode <= 5:
        while True:
            print("Enter room id: ")
            online_room = input()
            if not (online_room.isdigit() and int(online_room) >= 0):
                print("Invalid room id")
            else:
                online_room = int(online_room)
                break

    if mode == 1:
        print("Selected local mode")
        team_1_token = team_2_token = global_token = None
    elif mode == 2:
        print("Selected online mode, practice team 1 - team 2")
        global_token = team_1_token
    elif mode == 3:
        print("Selected online mode, practice swap team 1 - team 2 token")
        team_1_token, team_2_token = team_2_token, team_1_token
        global_token = team_1_token
    elif mode == 4:
        if competition_token is None:
            print("Competition token is not set")
            exit(1)
        print("Selected online mode, competition you = team 1")
        global_token = team_1_token = competition_token
        team_2_token = None
    elif mode == 5:
        if competition_token is None:
            print("Competition token is not set")
            exit(1)
        print("Selected online mode, competition you = team 2")
        global_token = team_2_token = competition_token
        team_1_token = None


def get_online_map_data(room_id: int):
    rooms_json = requests.get(f'{BASE_URL}/player/games',
                              headers={"Authorization": global_token}).json()

    rooms_json = json.loads(json.dumps(rooms_json),
                            object_hook=online_field_decoder)

    rooms = OnlineFieldRequestList.model_validate(rooms_json).root

    for room in rooms:
        if room.id == room_id:
            return room


def get_client_delay():
    samples = []

    for _ in range(3):
        call_time = datetime.now()
        server_time_json = requests.get(f'{BASE_URL}/player/time').json()
        server_time = datetime.fromisoformat(server_time_json['time'])
        offset = (server_time - call_time).total_seconds()
        print(offset)
        samples.append(offset)

    round_trips = 4
    res = sum(samples) / len(samples) / round_trips
    print(f"Avg delay: {res}")

    return res


def current_turn():
    if start_time is None:
        return 1
    compensation = 0.1  # it's better to be late than early
    return max(
        min(
            math.floor(((datetime.now() - start_time).total_seconds() +
                       client_delay - compensation) / time_per_turn) + 1,
            max_turn),
        1)


def remaining_turn_time():
    if start_time is None:
        return 999999
    if start_time > datetime.now():
        return (start_time - datetime.now()).total_seconds()

    if max_turn and start_time + timedelta(seconds=time_per_turn) * max_turn < datetime.now():
        return 0
    compensation = 0.1  # it's better to be late than early
    return time_per_turn - (((datetime.now() - start_time).total_seconds() +
                            client_delay - compensation) % time_per_turn)


def get_online_actions(room_id: int):
    actions_json = requests.get(f'{BASE_URL}/player/games/{room_id}/actions',
                                headers={"Authorization": global_token}).json()

    return OnlineActionResponseList.model_validate(actions_json)


load_cli()
### LOAD OFFLINE GAME ###
if mode == 1:
    game_options, game_map, craftsmen, craftsman_strid_to_intid_map, craftsman_intid_to_strid_map = load_offline_game(
        map_path)
    actions_by_turn = load_offline_actions(
        action_path, craftsman_strid_to_intid_map)

    game = Game(game_options, game_map, craftsmen)
    # for actions in actions_by_turn:
    #     for action in actions:
    #         game.addAction(action)
    #     game.nextTurn()
### END LOAD OFFLINE GAME ###
else:
    field_data = get_online_map_data(online_room)
    if (field_data is None):
        print("Room cannot be fetched")
        exit(1)

    client_delay = get_client_delay()

    time_per_turn = field_data.time_per_turn
    max_turn = field_data.num_of_turns

    if field_data.start_time is not None:
        start_time = field_data.start_time

    game_options, game_map, craftsmen, craftsman_strid_to_intid_map, craftsman_intid_to_strid_map = load_online_game(
        field_data)

    action_list_json = get_online_actions(online_room).root

    actions_by_turn = load_online_actions(
        action_list_json, craftsman_strid_to_intid_map)

    game = Game(game_options, game_map, craftsmen)

    if actions_by_turn:
        max_turn_to_apply = max(actions_by_turn.keys())

        for turn in range(2, max_turn_to_apply+1):
            if turn in actions_by_turn:
                for action in actions_by_turn[turn]:
                    game.addAction(action)
            game.nextTurn()

app = FastAPI()
session = aiohttp.ClientSession()

check_start_time_counter = 0

@app.on_event("startup")
@repeat_every(seconds=0.3)
async def auto_update_online_game_state():
    global start_time, field_data,check_start_time_counter
    if online_room < 0:
        return

    if start_time is None:
        check_start_time_counter += 1
        if check_start_time_counter % 10 == 0:
            print("Waiting for game to set a start time")
            field_data = get_online_map_data(online_room)
            if field_data.start_time is None:
                return
            start_time = field_data.start_time
            print("Game start time is set")

    local_game_state = game.getCurrentState()

    current_calculated_turn = current_turn()
    current_turn_time_left = remaining_turn_time()

    if local_game_state.turn != current_calculated_turn:
        if local_game_state.isT1Turn:
            command_buffer_t1.clear()
        else:
            command_buffer_t2.clear()

        action_list_json = get_online_actions(online_room)
        game_actions_by_turn = load_online_actions(
            action_list_json.root, craftsman_strid_to_intid_map)

        for turn_number in range(local_game_state.turn + 1, current_calculated_turn + 1):
            if turn_number in game_actions_by_turn:
                for action in game_actions_by_turn[turn_number]:
                    game.addAction(action)
            game.nextTurn()

        generate_builder_pos()

    else:
        # don't send commands unless if there is less than 1.0 seconds left
        if current_turn_time_left >= 1.0:  # seconds
            return
        if command_buffer_t1 and team_1_token is not None and local_game_state.isT1Turn:
            send_actions = list(map(lambda x: x[1], sorted(
                online_command_buffer_t1.items(),
                key=lambda id_and_command: command_order_t1[id_and_command[0]]
            )))

            # async post request is faster
            async with session.post(
                    f'{BASE_URL}/player/games/{online_room}/actions',
                    headers={"Authorization": team_1_token},
                    json={
                        "turn": local_game_state.turn + 1,
                        "actions": send_actions
                    }
            ) as res:
                if not (200 <= res.status < 300):
                    print(await res.text())
                else:
                    print("Sent online commands successfully")

        if command_buffer_t2 and team_2_token is not None and not local_game_state.isT1Turn:
            send_actions = list(map(lambda x: x[1], sorted(
                online_command_buffer_t2.items(),
                key=lambda id_and_command: command_order_t2[id_and_command[0]]
            )))

            async with session.post(
                    f'{BASE_URL}/player/games/{online_room}/actions',
                    headers={"Authorization": team_2_token},
                    json={
                        "turn": local_game_state.turn + 1,
                        "actions": send_actions
                    }
            ) as res:
                if not (200 <= res.status < 300):
                    print(await res.text())
                else:
                    print("Sent online commands successfully")


@app.post("/command")
async def do_command(command: CraftsmanCommand):
    global command_counter

    current_state = game.getCurrentState()
    craftsman_id = current_state.findCraftsmanIdByPos(
        *command.craftsman_pos)
    if craftsman_id < 0:
        raise HTTPException(400, detail="Craftsman not found")

    craftsman_is_t1 = current_state.craftsmen[craftsman_id].isT1

    selected_buffer = command_buffer_t1 if craftsman_is_t1 else command_buffer_t2
    selected_order = command_order_t1 if craftsman_is_t1 else command_order_t2

    selected_buffer[craftsman_id] = command

    if online_room >= 0:
        selected_online_buffer = online_command_buffer_t1 if craftsman_is_t1 else online_command_buffer_t2
        selected_online_buffer[craftsman_id] = local_command_to_online_action(
            command, game, craftsman_intid_to_strid_map)

    selected_order[craftsman_id] = command_counter

    command_counter += 1

    return "OK"


@app.post("/end_turn")
async def end_turn():
    global command_counter
    if online_room >= 0:
        # ONLINE MODE, noop
        return "OK"

    # LOCAL MODE
    is_t1_turn = game.getCurrentState().isT1Turn

    selected_buffer = command_buffer_t1 if is_t1_turn else command_buffer_t2
    selected_order = command_order_t1 if is_t1_turn else command_order_t2

    command_list_with_craftsman_id = sorted(
        selected_buffer.items(),
        key=lambda id_and_command: selected_order[id_and_command[0]]
    )

    for craftsman_id, command in command_list_with_craftsman_id:
        if command.action_type == PyActionType.STAY:
            continue

        action, subaction = local_action_to_cpp_action(
            command.action_type, command.direction)

        game.addAction(GameAction(
            craftsman_id,
            action,
            subaction
        ))

    game.nextTurn()
    selected_buffer.clear()

    generate_builder_pos()

    return "OK"


def generate_builder_pos():
    global command_counter
    game_state = game.getCurrentState()

    for (str_id, list_of_pos) in builder_pos_by_craftsman.items():
        if not list_of_pos:
            continue

        craftsman_local_id = craftsman_strid_to_intid_map[str_id]
        craftsman = game_state.craftsmen[craftsman_local_id]

        list_of_valid_pos = []
        for x, y in list_of_pos:
            if game_state.map.tiles[y][x] & ((1 << TileMask.POND.value) | (1 << TileMask.T1_CRAFTSMAN.value) | (1 << TileMask.T2_CRAFTSMAN.value)):
                continue

            if (craftsman.isT1 and game_state.map.tiles[y][x] & (1 << TileMask.T1_WALL.value)) or (not craftsman.isT1 and game_state.map.tiles[y][x] & (1 << TileMask.T2_WALL.value)):
                builder_pos_by_craftsman[str_id].remove((x, y))
                continue

            list_of_valid_pos.append((x, y))

        if not list_of_valid_pos:
            builder_pos_by_craftsman[str_id] = []
            continue

        cost, action = game.getCurrentState().findWayToBuild(
            craftsman.x, craftsman.y, craftsman.isT1, list_of_valid_pos)

        action_type, direction = cpp_action_to_local_action(
            action.actionType, action.subActionType)

        # turn build and move into destroy if there is a wall
        if action_type == PyActionType.BUILD or action_type == PyActionType.MOVE:
            (action_offset_x, action_offset_y) = get_direction_vector(direction)
            (target_x, target_y) = (craftsman.x + action_offset_x, craftsman.y + action_offset_y)

            if not (0 <= target_x < len(game_state.map.tiles[0]) and 0 <= target_y < len(game_state.map.tiles)):
                continue

            if (craftsman.isT1 and game_state.map.tiles[target_y][target_x] & (1 << TileMask.T2_WALL.value)) \
                    or (not craftsman.isT1 and game_state.map.tiles[target_y][target_x] & (1 << TileMask.T1_WALL.value)):
                # prevent diagonal destroy
                if action_type == PyActionType.MOVE and abs(action_offset_x) + abs(action_offset_y) > 1:
                    continue
                action_type = PyActionType.DESTROY


        print(cost, action)

        selected_buffer = command_buffer_t1 if craftsman.isT1 else command_buffer_t2
        selected_order = command_order_t1 if craftsman.isT1 else command_order_t2

        selected_buffer[craftsman_local_id] = CraftsmanCommand(
            craftsman_pos=(craftsman.x, craftsman.y),
            action_type=action_type,
            direction=direction
        )
        if online_room >= 0:
            selected_online_buffer = online_command_buffer_t1 if craftsman.isT1 else online_command_buffer_t2
            selected_online_buffer[craftsman_local_id] = local_command_to_online_action(
                selected_buffer[craftsman_local_id], game, craftsman_intid_to_strid_map)

        selected_order[craftsman_local_id] = command_counter
        command_counter += 1


@app.get("/current_state")
async def current_state():
    game_state = game.getCurrentState()

    map_state = game_state.map.tiles

    craftsmen = []

    for craftsman in game_state.craftsmen.values():
        craftsmen.append({
            "team": "team1" if craftsman.isT1 else "team2",
            "pos": (craftsman.x, craftsman.y),
            "id": craftsman_intid_to_strid_map[craftsman.id],
        })

    actions_to_be_applied = []

    command_list_with_craftsman_id = [
        *command_buffer_t1.items(),
        *command_buffer_t2.items()
    ]

    for craftsman_id, command in command_list_with_craftsman_id:
        if command.direction is None:
            continue
        craftsman = game_state.craftsmen[craftsman_id]
        dir_vec = get_direction_vector(command.direction)

        actions_to_be_applied.append({
            'pos': (craftsman.x + dir_vec[0], craftsman.y + dir_vec[1]),
            'action_type': command.action_type,
        })

    res = {
        "score": calculate_score(map_state, game_options),
        "state": {
            "turn_number": game_state.turn,
            "turn_state": "team1_turn" if game_state.isT1Turn else "team2_turn",
            "map": map_state[:game.gameOptions.mapHeight][:game.gameOptions.mapWidth],
            "craftsmen": craftsmen,
        },
        "game_status": {
            "remaining": remaining_turn_time(),
        },
        "options": {
            "map_width": game.gameOptions.mapWidth,
            "map_height": game.gameOptions.mapHeight,
        },
        "builder_pos_by_craftsman": builder_pos_by_craftsman,
        "actions_to_be_applied": actions_to_be_applied,
    }

    return res


class BuilderCommand(BaseModel):
    action: str
    id: Union[str, None] = None
    pos: Union[tuple[int, int], None] = None


@app.post("/builder")
async def builder(command: BuilderCommand):
    if command.action == "build":
        if command.id not in builder_pos_by_craftsman:
            builder_pos_by_craftsman[command.id] = []
        if command.pos not in builder_pos_by_craftsman[command.id]:
            if len(builder_pos_by_craftsman[command.id]) >= 12:
                return "Too many builder pos"
            builder_pos_by_craftsman[command.id].append(command.pos)
    elif command.action == "unbuild":
        if command.pos is None:
            builder_pos_by_craftsman[command.id] = []
        elif command.id in builder_pos_by_craftsman and command.pos in builder_pos_by_craftsman[command.id]:
            builder_pos_by_craftsman[command.id].remove(command.pos)
    elif command.action == "unbuild_all":
        builder_pos_by_craftsman.clear()

    return "OK"


@app.post("/generate_builder_pos")
async def generate_builder_pos_endpoint():
    generate_builder_pos()
    return "OK"