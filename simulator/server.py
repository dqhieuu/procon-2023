import asyncio
from copy import deepcopy

from fastapi import FastAPI

from ai.ai import dijkstra, CentralizedCritic, CraftsmanAgent
from entities.craftsman import CraftsmanCommand, get_craftsman_at
from entities.utils.enums import Team, TurnState
from game import Game
import requests

from utils import numpy_game_map_to_list_from_history

game = Game("assets/map2.txt")
app = FastAPI()

online_room = 0
team_1_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTUsIm5hbWUiOiJQUk9DT04gVUVUIDEiLCJpc19hZG1pbiI6ZmFsc2UsImlhdCI6MTY4NzE2NTU4MH0.Uf5GgnVVNxKq2N-63xt7myYbvz_nakg90ANtrCrxIAA"
team_2_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTYsIm5hbWUiOiJQUk9DT04gVUVUIDIgIiwiaXNfYWRtaW4iOmZhbHNlLCJpYXQiOjE2ODcxODY3NDl9.U2IQh3PhWTcmLuws0oEmfp-Oo8GES6Yfg8pAIUcIkfE"

@app.post("/command")
async def do_command(command: CraftsmanCommand):
    if online_room > 0:
        r = requests.post('https://procon2023.duckdns.org/api/command', headers={"Authorization": team_1_token},
                          json=command.dict())
        return r.json()

    game.add_command(command)
    return "OK"


@app.post("/end_turn")
async def end_turn():
    game.process_turn()


@app.get("/current_state")
async def current_state():
    if online_room > 0:
        r = requests.get('https://procon2023.duckdns.org/api/', headers={"Authorization": team_1_token})
        return r.json()

    state_jsonable = deepcopy(game.current_state)
    state_jsonable.map.map = state_jsonable.map.map.tolist()

    return {
        "score": game.score,
        "state": state_jsonable
    }


@app.get("/history")
async def current_state():
    return numpy_game_map_to_list_from_history(game.history)

@app.get("/path")
async def path(x: int, y: int, simple: bool = False):
    c = get_craftsman_at(game.current_state.craftsmen, (x, y))
    if c is None:
        return []
    return dijkstra(c, game.current_state.map, pathOnlyNextMove=simple).tolist()

@app.get("/auto")
async def auto():
    team1_critic = CentralizedCritic(Team.TEAM1, game)
    team1_craftsmen = [c for c in game.current_state.craftsmen if c.team == Team.TEAM1]
    team1_craftsman_agents = [CraftsmanAgent(c, game,team1_critic) for c in team1_craftsmen]
    team1_critic.team_agents = team1_craftsman_agents

    team2_critic = CentralizedCritic(Team.TEAM2, game)
    team2_craftsmen = [c for c in game.current_state.craftsmen if c.team == Team.TEAM2]
    team2_craftsman_agents = [CraftsmanAgent(c, game,team2_critic) for c in team2_craftsmen]
    team2_critic.team_agents = team2_craftsman_agents

    while not game.is_game_over:
        if game.current_state.turn_state == TurnState.TEAM1_TURN:
            team1_critic.act()
        elif game.current_state.turn_state == TurnState.TEAM2_TURN:
            team2_critic.act()

        game.process_turn()


asyncio.run(auto())


