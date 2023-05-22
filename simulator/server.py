from fastapi import FastAPI

from entities.craftman import CraftmanCommand
from game import Game

game = Game("assets/map1.txt")
app = FastAPI()


@app.post("/command")
async def do_command(command: CraftmanCommand):
    game.add_command(command)
    return "OK"


@app.post("/end_turn")
async def end_turn():
    return game.process_turn()


@app.get("/current_state")
async def current_state():
    return game.current_state
