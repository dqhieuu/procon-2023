from fastapi import FastAPI

from entities.craftman import CraftmanCommand
from game import Game

game = Game("assets/map1.txt")
app = FastAPI()


# PPO vs SAC (on vs off policy)


@app.post("/command")
async def command(command: CraftmanCommand):
    game.add_command(command)
    return "OK"


@app.post("/end_turn")
async def end_turn():
    return game.process_turn()
