import json
import re
from copy import deepcopy
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi_restful.tasks import repeat_every

from ai.ai import dijkstra, CentralizedCritic, CraftsmanAgent
from ai.ai_request import AIStrategyRequest, AIStrategyEnum
from simulator_new.old.entities.craftsman import CraftsmanCommand, get_craftsman_at
from simulator_new.old.entities import Team, TurnState, ActionType, Direction, get_direction_vector
from simulator_new.old.game import Game
import requests

from online import OnlineFieldRequestList, online_field_decoder, OnlineActionResponseList, OnlineGameStatus, \
    OnlineEnumAction, local_command_to_online_action
from utils import numpy_game_map_to_list_from_history
import aiohttp

### SET THESE VARIABLES ###
BASE_URL = "https://procon2023.duckdns.org/api"

competition_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzcsIm5hbWUiOiJVRVQgQWRtaW4iLCJpc19hZG1pbiI6dHJ1ZSwiaWF0IjoxNzAwMTQ3MTIwLCJleHAiOjE3MDAzMTk5MjB9.R2ALaML-k7bNRESeHXuhdzMxuWTbDCw556PhI2wrWa8"
team_1_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NTUsIm5hbWUiOiJ1ZXQxIiwiaXNfYWRtaW4iOmZhbHNlLCJpYXQiOjE3MDA5MDYyNzIsImV4cCI6MTcwMTA3OTA3Mn0.XbFpB8SiDU-1NElyyJxKDSiVW__0k5DgHe56eGzCU8w"
team_2_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NTYsIm5hbWUiOiJ1ZXQyIiwiaXNfYWRtaW4iOmZhbHNlLCJpYXQiOjE3MDA5MDYyODgsImV4cCI6MTcwMTA3OTA4OH0.rggpoLUP48CQimFAvTLLxU_hpAP3EKI-liIM_ln3ceE"
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

online_command_dict_per_craftsman_team1: dict[str, dict[str,str]] = {}
online_command_dict_per_craftsman_team2: dict[str, dict[str,str]] = {}

# load AI
team1_critic = None
if team_1_token is not None or mode == 1:
    team1_critic = CentralizedCritic(Team.TEAM1, game)
    _team1_craftsmen = [c for c in game.current_state.craftsmen if c.team == Team.TEAM1]
    _team1_craftsman_agents = [CraftsmanAgent(c.id, game, team1_critic) for c in _team1_craftsmen]
    team1_critic.team_agents = _team1_craftsman_agents

team2_critic = None
if team_2_token is not None or mode == 1:
    team2_critic = CentralizedCritic(Team.TEAM2, game)
    _team2_craftsmen = [c for c in game.current_state.craftsmen if c.team == Team.TEAM2]
    _team2_craftsman_agents = [CraftsmanAgent(c.id, game, team2_critic) for c in _team2_craftsmen]
    team2_critic.team_agents = _team2_craftsman_agents


app = FastAPI()
session = aiohttp.ClientSession()


@app.post("/command")
async def do_command(command: CraftsmanCommand):
    if online_room > 0:
        # ONLINE MODE
        craftsman = get_craftsman_at(game.current_state.craftsmen, command.craftsman_pos)
        craftsman_id = craftsman.id
        if craftsman_id is None:
            raise HTTPException(400, "Craftsman not found")

        online_command = local_command_to_online_action(command, game)

        if craftsman.team == Team.TEAM1:
            online_command_dict_per_craftsman_team1[craftsman_id] = online_command
        elif craftsman.team == Team.TEAM2:
            online_command_dict_per_craftsman_team2[craftsman_id] = online_command

        return "OK"
    else:
        # LOCAL MODE
        game.add_command(command)
        return "OK"


@app.post("/end_turn")
async def end_turn():
    if online_room > 0:
        # ONLINE MODE
        return "OK"
    else:
        # LOCAL MODE
        game.process_turn()
        await team1_critic.act()
        await team2_critic.act()


@app.post("/ai_strategy")
async def ai_strategy(strategy: AIStrategyRequest):
    if team1_critic is not None:
        team1_critic.update_agent_strategy(strategy)
    if team2_critic is not None:
        team2_critic.update_agent_strategy(strategy)


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

    agent_list = []
    if team1_critic is not None:
        agent_list += team1_critic.team_agents
    if team2_critic is not None:
        agent_list += team2_critic.team_agents

    agent_strategy_list = []
    for agent in agent_list:
        detail = {}
        if agent.current_strategy == AIStrategyEnum.MANUAL:
            detail = {
                'destination': agent.manual_destination,
            }
        elif agent.current_strategy == AIStrategyEnum.CAPTURE_CASTLE:
            detail = {
                'castle_pos': agent.selected_castle_pos,
            }
        elif agent.current_strategy == AIStrategyEnum.EXPAND_TERRITORY:
            detail = {
                'pivot_pos': agent.expand_pivot_pos,
                'step': agent.expand_step,
                'esm_offset': agent.esm_offset,
                # 'esm': agent._expand_strategy_matrix.tolist(),
            }

        agent_strategy_list.append({
            'craftsman_id': agent.craftsman_id,
            'craftsman_pos': agent.craftsman.pos,
            'strategy': agent.current_strategy,
            'detail': detail
        })

    res['agent_strategy_list'] = agent_strategy_list

    return res


@app.on_event("startup")
@repeat_every(seconds=0.5)
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

            if game.current_state.turn_state == TurnState.TEAM1_TURN and team1_critic is not None:
                await team1_critic.act()
            elif game.current_state.turn_state == TurnState.TEAM2_TURN and team2_critic is not None:
                await team2_critic.act()
        else:

            if len(online_command_dict_per_craftsman_team1) > 0 and team_1_token is not None:
                if game_status.remaining >= 2:
                    return  # wait for next second to send command

                # async post request is faster
                async with session.post(
                        '{}/player/games/{}/actions'.format(BASE_URL, online_room),
                        headers={"Authorization": team_1_token},
                        json={
                            "turn": game.current_state.turn_number + (1 if game.current_state.turn_state == TurnState.TEAM1_TURN else 2),
                            "actions": list(online_command_dict_per_craftsman_team1.values()),
                        }) as res:
                    if not (200 <= res.status < 300):
                        print(await res.text())
                    else:
                        print("Sent online commands successfully")

            if len(online_command_dict_per_craftsman_team2) > 0 and team_2_token is not None:
                if game_status.remaining >= 2:
                    return  # wait for next second to send command

                async with session.post(
                        '{}/player/games/{}/actions'.format(BASE_URL, online_room),
                        headers={"Authorization": team_2_token},
                        json={
                            "turn": game.current_state.turn_number + (1 if game.current_state.turn_state == TurnState.TEAM2_TURN else 2),
                            "actions": list(online_command_dict_per_craftsman_team2.values()),
                        }) as res:
                    if not (200 <= res.status < 300):
                        print(await res.text())
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
    if online_room > 0:
        return "OK"
    while not game.is_game_over:
        if game.current_state.turn_state == TurnState.TEAM1_TURN:
            await team1_critic.act()
        elif game.current_state.turn_state == TurnState.TEAM2_TURN:
            await team2_critic.act()

        game.process_turn()
