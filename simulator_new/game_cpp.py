from contextlib import asynccontextmanager
import json
import re
from typing import Any
import requests
from bin.game_interfaces_binding import Game, GameAction
from online import OnlineActionResponseList, OnlineGameStatus, OnlineFieldRequestList, load_online_actions, load_online_game, local_command_to_online_action, online_field_decoder
from utils import get_direction_vector

from utils_cpp import load_offline_game, load_offline_actions, calculate_score, local_action_to_cpp_action
from fastapi import FastAPI, HTTPException
from fastapi_restful.tasks import repeat_every
from model import CraftsmanCommand, PyActionType
import aiohttp


### SET THESE VARIABLES ###
BASE_URL = "https://procon2023.duckdns.org/api"

competition_token = None
team_1_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzcsIm5hbWUiOiJVRVQgQWRtaW4iLCJpc19hZG1pbiI6dHJ1ZSwiaWF0IjoxNzAxNDQ1MzI4LCJleHAiOjE3MDE2MTgxMjh9.pY0oLug_H_IxqWvHTKYFc_7zt2FIaIxXHamHpH51vAo"
team_2_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzcsIm5hbWUiOiJVRVQgQWRtaW4iLCJpc19hZG1pbiI6dHJ1ZSwiaWF0IjoxNzAxNDQ1MzI4LCJleHAiOjE3MDE2MTgxMjh9.pY0oLug_H_IxqWvHTKYFc_7zt2FIaIxXHamHpH51vAo"
### END SET THESE VARIABLES ###

global_token = None
online_room = -1

print("""
SELECT A MODE:
1. Local
2. Online, practice: team A - team B
3. Online, practice: swap team A - team B token
4. Online, competition: you = team A
5. Online, competition: you = team B
""")

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


is_negative_turn = re.compile(r'turn: -')


def get_game_status(room_id: int):
    game_status_json = requests.get(f'{BASE_URL}/player/games/{room_id}/status',
                                    headers={"Authorization": global_token}).json()

    if game_status_json.get('detail'):
        if is_negative_turn.search(game_status_json['detail']):
            # game has not started yet
            print("Game has not started yet")
            return OnlineGameStatus(cur_turn=0, max_turn=999, remaining=999)
        else:
            print("Some other error")
            return OnlineGameStatus(cur_turn=0, max_turn=999, remaining=999)
    return OnlineGameStatus.model_validate(game_status_json)


def get_online_actions(room_id: int):
    actions_json = requests.get(f'{BASE_URL}/player/games/{room_id}/actions',
                                headers={"Authorization": global_token}).json()

    return OnlineActionResponseList.model_validate(actions_json)


### LOAD OFFLINE GAME ###
action_path = "test-cases/match-249.txt"
map_path = "test-cases/map-249-game-2.txt"

if mode == 1:
    game_options, game_map, craftsmen, craftsman_strid_to_intid_map = load_offline_game(
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
    game_options, game_map, craftsmen, craftsman_strid_to_intid_map = load_online_game(
        field_data)

    action_list_json = get_online_actions(online_room).root

    actions_by_turn = load_online_actions(
        action_list_json, craftsman_strid_to_intid_map)

    game = Game(game_options, game_map, craftsmen)

    if actions_by_turn:
        max_turn = max(actions_by_turn.keys())

        for turn in range(1, max_turn):
            if turn not in actions_by_turn:
                game.nextTurn()
                continue

            for action in actions_by_turn[turn]:
                game.addAction(action)
            game.nextTurn()

command_buffer_t1: dict[int, CraftsmanCommand] = {}
command_buffer_t2: dict[int, CraftsmanCommand] = {}

command_counter = 0
command_order_t1: dict[int, int] = {}
command_order_t2: dict[int, int] = {}

online_command_buffer_t1: dict[str, dict[str, Any]] = {}
online_command_buffer_t2: dict[str, dict[str, Any]] = {}

game_status = 'test'


app = FastAPI()
session = aiohttp.ClientSession()


@asynccontextmanager
@repeat_every(seconds=0.5)
async def auto_update_online_game_state():

    if online_room < 0:
        return

    global game_status
    print(game_status, game.current_state.turn_number)

    game_status = get_game_status(online_room)

    local_game_state = game.getCurrentState()

    if local_game_state.turn != game_status.cur_turn:
        if local_game_state.isT1Turn:
            command_buffer_t2.clear()
        else:
            command_buffer_t1.clear()

        action_list_json = get_online_actions(online_room)
        game_actions_by_turn = load_online_actions(
            action_list_json.root, craftsman_strid_to_intid_map)

        for turn in range(local_game_state.turn + 1, game_status.cur_turn + 1):
            if turn not in game_actions_by_turn:
                game.nextTurn()
                continue

            for action in game_actions_by_turn[turn]:
                game.addAction(action)
            game.nextTurn()

    else:
        if command_buffer_t1 and team_1_token is not None:
            if game_status.remaining >= 2:  # seconds
                return  # wait for next second to send command

            send_actions = list(map(lambda x: x[1], sorted(
                online_command_buffer_t1.items(),
                key=lambda id_and_command: command_order_t1[id_and_command[0]]
            )))

            # async post request is faster
            async with session.post(
                    f'{BASE_URL}/player/games/{online_room}/actions',
                    headers={"Authorization": team_1_token},
                    json={
                        "turn": local_game_state.turn + (1 if local_game_state.isT1Turn else 2),
                        "actions": send_actions
                    }) as res:
                if not (200 <= res.status < 300):
                    print(await res.text())
                else:
                    print("Sent online commands successfully")

        if command_buffer_t2 and team_2_token is not None:
            if game_status.remaining >= 2:
                return

            send_actions = list(map(lambda x: x[1], sorted(
                online_command_buffer_t2.items(),
                key=lambda id_and_command: command_order_t2[id_and_command[0]]
            )))

            async with session.post(
                    f'{BASE_URL}/player/games/{online_room}/actions',
                    headers={"Authorization": team_2_token},
                    json={
                        "turn": local_game_state.turn + (1 if not local_game_state.isT1Turn else 2),
                        "actions": send_actions
                    }) as res:
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
    selected_online_buffer = online_command_buffer_t1 if craftsman_is_t1 else online_command_buffer_t2
    selected_order = command_order_t1 if craftsman_is_t1 else command_order_t2

    selected_buffer[craftsman_id] = command

    if online_room >= 0:
        selected_online_buffer[craftsman_id] = local_command_to_online_action(
            command, game, craftsman_strid_to_intid_map)

    selected_order[craftsman_id] = command_counter

    command_counter += 1

    return "OK"


@app.post("/end_turn")
async def end_turn():
    if online_room > 0:
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
