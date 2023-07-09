import json
from copy import deepcopy

from fastapi import FastAPI
from fastapi_restful.tasks import repeat_every

from ai.ai import dijkstra, CentralizedCritic, CraftsmanAgent
from entities.craftsman import CraftsmanCommand, get_craftsman_at
from entities.utils.enums import Team, TurnState
from game import Game
import requests

from online import OnlineFieldRequestList, online_field_decoder, OnlineActionResponseList, OnlineGameStatus
from utils import numpy_game_map_to_list_from_history



online_room = 57

global_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTYsIm5hbWUiOiJQUk9DT04gVUVUIDIgIiwiaXNfYWRtaW4iOmZhbHNlLCJpYXQiOjE2ODcxODY3NDl9.U2IQh3PhWTcmLuws0oEmfp-Oo8GES6Yfg8pAIUcIkfE"

team_1_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTUsIm5hbWUiOiJQUk9DT04gVUVUIDEiLCJpc19hZG1pbiI6ZmFsc2UsImlhdCI6MTY4NzE2NTU4MH0.Uf5GgnVVNxKq2N-63xt7myYbvz_nakg90ANtrCrxIAA"
team_2_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTYsIm5hbWUiOiJQUk9DT04gVUVUIDIgIiwiaXNfYWRtaW4iOmZhbHNlLCJpYXQiOjE2ODcxODY3NDl9.U2IQh3PhWTcmLuws0oEmfp-Oo8GES6Yfg8pAIUcIkfE"

BASE_URL = "https://procon2023.duckdns.org/api"


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


def get_online_actions(room_id):
    actions_json = requests.get('{}/player/games/{}/actions'.format(BASE_URL, online_room),
                                headers={"Authorization": global_token}).json()
    return OnlineActionResponseList.parse_obj(actions_json)


game = Game("assets/map2.txt") if online_room <= 0 else Game()
if online_room > 0:
    game.load_online_map(get_online_map_data(online_room))
    game.load_online_action_list(get_online_actions(online_room))


app = FastAPI()

@app.post("/command")
async def do_command(command: CraftsmanCommand):
    if online_room > 0:
        r = requests.post('https://procon2023.duckdns.org/api/player/games/{}/actions'.format(online_room),
                          headers={"Authorization": team_1_token})
        return r.json()

    game.add_command(command)
    return "OK"


@app.post("/end_turn")
async def end_turn():
    game.process_turn()


@app.get("/current_state")
async def current_state():
    # if online_room > 0:
    #     field = get_online_map_data(online_room),
    #
    #     # actions_json = requests.get('https://procon2023.duckdns.org/api/player/games/{}/actions'.format(online_room),
    #     #                             headers={"Authorization": team_2_token}).json()
    #     #
    #     # actions = OnlineActionResponseList.parse_obj(actions_json)
    #
    #     return {"field": field, "actions": actions}

    state_jsonable = deepcopy(game.current_state)
    state_jsonable.map.map = state_jsonable.map.map.tolist()

    res = {
        "score": game.score,
        "state": state_jsonable
    }

    if game.is_game_over:
        res["winner"] = game.winning_team

    return res


@app.on_event("startup")
@repeat_every(seconds=0.3)
async def get_game_status():
    if online_room > 0:
        r = requests.get('https://procon2023.duckdns.org/api/player/games/{}/status'.format(online_room),
                          headers={"Authorization": team_2_token})
        json = r.json()
        if json.get('detail'):
            print("game ended", json)
            return
        status = OnlineGameStatus.parse_obj(json)
        print(status)

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
