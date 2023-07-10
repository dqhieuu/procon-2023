import json
import re
from copy import deepcopy
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi_restful.tasks import repeat_every

from ai.ai import dijkstra, CentralizedCritic, CraftsmanAgent
from entities.craftsman import CraftsmanCommand, get_craftsman_at
from entities.utils.enums import Team, TurnState, ActionType, Direction, get_direction_vector
from game import Game
import requests

from online import OnlineFieldRequestList, online_field_decoder, OnlineActionResponseList, OnlineGameStatus, \
    OnlineEnumAction
from utils import numpy_game_map_to_list_from_history
import aiohttp

### SET THESE VARIABLES ###
BASE_URL = "https://procon2023.duckdns.org/api"

competition_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTUsIm5hbWUiOiJQUk9DT04gVUVUIDEiLCJpc19hZG1pbiI6ZmFsc2UsImlhdCI6MTY4ODg5MjI0NiwiZXhwIjoxNjg5MDY1MDQ2fQ.rKpQyVo_EiJ7b-bbmu9zDxzfMhjv-X-OLIFcLkcNRbs"
team_1_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTUsIm5hbWUiOiJQUk9DT04gVUVUIDEiLCJpc19hZG1pbiI6ZmFsc2UsImlhdCI6MTY4ODg5MjI0NiwiZXhwIjoxNjg5MDY1MDQ2fQ.rKpQyVo_EiJ7b-bbmu9zDxzfMhjv-X-OLIFcLkcNRbs"
team_2_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTYsIm5hbWUiOiJQUk9DT04gVUVUIDIgIiwiaXNfYWRtaW4iOmZhbHNlLCJpYXQiOjE2ODg4OTIyNjMsImV4cCI6MTY4OTA2NTA2M30.phqhY5a8ox0ObRa-vXn5T6JHIO5Cl3BEJUo2-a6BK4E"
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

mode = int(input())
if not 1 <= mode <= 5:
    print("Invalid mode")
    exit(1)

if 2 <= mode <= 5:
    print("Enter room id: ")
    online_room = int(input())
    if online_room < 0:
        print("Invalid room id")
        exit(1)

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


def get_online_map_data(room_id):
    rooms_json = requests.get('{}/player/games'.format(BASE_URL, online_room),
                              headers={"Authorization": global_token}).json()
    rooms_json = json.loads(json.dumps(rooms_json), object_hook=online_field_decoder)
    rooms = OnlineFieldRequestList.parse_obj(rooms_json).__root__
    selected_room = None
    for room in rooms:
        if room.id == room_id:
            selected_room = room
    return selected_room


is_negative_turn = re.compile(r'turn: -')


def get_game_status(room_id):
    game_status_json = requests.get('{}/player/games/{}/status'.format(BASE_URL, room_id),
                     headers={"Authorization": global_token}).json()

    if game_status_json.get('detail'):
        if is_negative_turn.search(game_status_json['detail']):
            # game has not started yet
            print("Game has not started yet")
            return OnlineGameStatus(cur_turn=0, max_turn=999, remaining=999)
        else:
            return None
    return OnlineGameStatus.parse_obj(game_status_json)


def get_online_actions(room_id):
    actions_json = requests.get('{}/player/games/{}/actions'.format(BASE_URL, online_room),
                                headers={"Authorization": global_token}).json()

    return OnlineActionResponseList.parse_obj(actions_json)


game_status: Optional[OnlineGameStatus] = None
game = Game("assets/map2.txt") if online_room <= 0 else Game()
if online_room > 0:
    game.load_online_map(get_online_map_data(online_room))
    game_status = get_game_status(online_room)
    game.load_online_action_list(get_online_actions(online_room), game_status)

app = FastAPI()

online_command_dict_per_craftsman_team1: dict[str, dict[str,str]] = {}
online_command_dict_per_craftsman_team2: dict[str, dict[str,str]] = {}


@app.post("/command")
async def do_command(command: CraftsmanCommand):
    if online_room > 0:
        craftsman = get_craftsman_at(game.current_state.craftsmen, command.craftsman_pos)
        craftsman_id = craftsman.id
        if craftsman_id is None:
            raise HTTPException(400, "Craftsman not found")

        online_command = {
            'craftsman_id': craftsman_id,
            'action': 'STAY'
        }

        if command.action_type is ActionType.MOVE and command.direction in [Direction.UP, Direction.DOWN,
                                                                            Direction.LEFT, Direction.RIGHT,
                                                                            Direction.UP_LEFT, Direction.UP_RIGHT,
                                                                            Direction.DOWN_LEFT, Direction.DOWN_RIGHT]:
            online_command['action'] = 'MOVE'
            if command.direction == Direction.UP:
                online_command['action_param'] = 'UP'
            elif command.direction == Direction.DOWN:
                online_command['action_param'] = 'DOWN'
            elif command.direction == Direction.LEFT:
                online_command['action_param'] = 'LEFT'
            elif command.direction == Direction.RIGHT:
                online_command['action_param'] = 'RIGHT'
            elif command.direction == Direction.UP_LEFT:
                online_command['action_param'] = 'UPPER_LEFT'
            elif command.direction == Direction.UP_RIGHT:
                online_command['action_param'] = 'UPPER_RIGHT'
            elif command.direction == Direction.DOWN_LEFT:
                online_command['action_param'] = 'LOWER_LEFT'
            elif command.direction == Direction.DOWN_RIGHT:
                online_command['action_param'] = 'LOWER_RIGHT'
        elif command.action_type in [ActionType.BUILD, ActionType.DESTROY] and command.direction in [Direction.UP,
                                                                                                     Direction.DOWN,
                                                                                                     Direction.LEFT,
                                                                                                     Direction.RIGHT]:
            if command.action_type is ActionType.BUILD:
                online_command['action'] = 'BUILD'
            elif command.action_type is ActionType.DESTROY:
                online_command['action'] = 'DESTROY'

            if command.direction == Direction.UP:
                online_command['action_param'] = 'ABOVE'
            elif command.direction == Direction.DOWN:
                online_command['action_param'] = 'BELOW'
            elif command.direction == Direction.LEFT:
                online_command['action_param'] = 'LEFT'
            elif command.direction == Direction.RIGHT:
                online_command['action_param'] = 'RIGHT'

        if craftsman.team == Team.TEAM1:
            online_command_dict_per_craftsman_team1[craftsman_id] = online_command
        elif craftsman.team == Team.TEAM2:
            online_command_dict_per_craftsman_team2[craftsman_id] = online_command

        return "OK"

    game.add_command(command)
    return "OK"


@app.post("/end_turn")
async def end_turn():
    if online_room > 0:
        return "OK"
    game.process_turn()


@app.get("/current_state")
async def current_state():
    state_jsonable = deepcopy(game.current_state)
    state_jsonable.map.map = state_jsonable.map.map.tolist()

    res = {
        "score": game.score,
        "state": state_jsonable
    }

    if game_status is not None:
        res["game_status"] = game_status

    if game.is_game_over:
        res["winner"] = game.winning_team

    actions_to_be_applied: dict[str, dict[str, str]] = {
        **online_command_dict_per_craftsman_team1,
        **online_command_dict_per_craftsman_team2,
    }

    actions_to_be_applied_list = []
    for craftsman_id, action in actions_to_be_applied.items():
        if action.get('action_param') is None:
            continue
        craftsman = game.find_craftsman_by_id(craftsman_id)

        dir_vec = get_direction_vector(Direction.from_online_type(action['action_param']))
        action_type = ActionType.from_online_type(OnlineEnumAction(action['action']))
        actions_to_be_applied_list.append({
            'pos': (craftsman.pos[0] + dir_vec[0], craftsman.pos[1] + dir_vec[1]),
            'action_type': action_type
        })

    res['actions_to_be_applied'] = actions_to_be_applied_list

    return res


@app.on_event("startup")
@repeat_every(seconds=0.3)
async def auto_update_online_game_state():
    global game_status
    print(game_status, game.current_state.turn_number)
    if online_room > 0:
        game_status = get_game_status(online_room)

        if game.current_state.turn_number != game_status.cur_turn:
            game.load_online_action_list(
                action_list=get_online_actions(online_room),
                current_game_status=game_status
            )
            if game.current_state.turn_state == TurnState.TEAM1_TURN:
                online_command_dict_per_craftsman_team2.clear()
            elif game.current_state.turn_state == TurnState.TEAM2_TURN:
                online_command_dict_per_craftsman_team1.clear()
        else:
            if len(online_command_dict_per_craftsman_team1) > 0 and team_1_token is not None:
                # async post request is faster
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                            '{}/player/games/{}/actions'.format(BASE_URL, online_room),
                            headers={"Authorization": team_1_token},
                            json={
                                "turn": game.current_state.turn_number + (1 if game.current_state.turn_state == TurnState.TEAM1_TURN else 2),
                                "actions": list(online_command_dict_per_craftsman_team1.values()),
                            }) as res:
                        if not (200 <= res.status < 300):
                            print(res.text)
                        else:
                            print("Sent online commands successfully")

            if len(online_command_dict_per_craftsman_team2) > 0 and team_2_token is not None:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                            '{}/player/games/{}/actions'.format(BASE_URL, online_room),
                            headers={"Authorization": team_2_token},
                            json={
                                "turn": game.current_state.turn_number + (1 if game.current_state.turn_state == TurnState.TEAM2_TURN else 2),
                                "actions": list(online_command_dict_per_craftsman_team2.values()),
                            }) as res:
                        if not (200 <= res.status < 300):
                            print(res.text)
                        else:
                            print("Sent online commands successfully")


@app.get("/history")
async def current_state():
    return numpy_game_map_to_list_from_history(game.history)


@app.get("/path")
async def path(x: int, y: int, simple: bool = False):
    c = get_craftsman_at(game.current_state.craftsmen, (x, y))
    if c is None:
        return []
    return dijkstra(c, game.current_state.map, save_only_one_next_move_in_path=simple).tolist()


@app.get("/auto")
async def auto():
    team1_critic = CentralizedCritic(Team.TEAM1, game)
    team1_craftsmen = [c for c in game.current_state.craftsmen if c.team == Team.TEAM1]
    team1_craftsman_agents = [CraftsmanAgent(c.id, game, team1_critic) for c in team1_craftsmen]
    team1_critic.team_agents = team1_craftsman_agents

    team2_critic = CentralizedCritic(Team.TEAM2, game)
    team2_craftsmen = [c for c in game.current_state.craftsmen if c.team == Team.TEAM2]
    team2_craftsman_agents = [CraftsmanAgent(c.id, game, team2_critic) for c in team2_craftsmen]
    team2_critic.team_agents = team2_craftsman_agents

    while not game.is_game_over:
        if game.current_state.turn_state == TurnState.TEAM1_TURN:
            team1_critic.act()
        elif game.current_state.turn_state == TurnState.TEAM2_TURN:
            team2_critic.act()

        game.process_turn()
