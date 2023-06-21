from fastapi import FastAPI

from entities.craftman import CraftmanCommand
from game import Game
import requests

game = Game("assets/map1.txt")
app = FastAPI()

online_room = 15
team_1_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTUsIm5hbWUiOiJQUk9DT04gVUVUIDEiLCJpc19hZG1pbiI6ZmFsc2UsImlhdCI6MTY4NzE2NTU4MH0.Uf5GgnVVNxKq2N-63xt7myYbvz_nakg90ANtrCrxIAA"
team_2_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTYsIm5hbWUiOiJQUk9DT04gVUVUIDIgIiwiaXNfYWRtaW4iOmZhbHNlLCJpYXQiOjE2ODcxODY3NDl9.U2IQh3PhWTcmLuws0oEmfp-Oo8GES6Yfg8pAIUcIkfE"


@app.post("/command")
async def do_command(command: CraftmanCommand):
    game.add_command(command)
    return "OK"


@app.post("/end_turn")
async def end_turn():
    return game.process_turn()


@app.get("/current_state")
async def current_state():
    if online_room > 0:
        r = requests.get('https://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))

    return game.current_state
