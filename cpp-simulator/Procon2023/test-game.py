# %%
from bin.game_interfaces_binding import *

# %%
action_path = "test-cases/match-395.txt"
map_path = "test-cases/map-395-ctu-12-11-game-1.txt"

# %%
from utils import load_map

mapdata = load_map(map_path)

# %%
def map_tile_to_bitmask(tile):
    if tile == 1:
        return 1 << TileMask.POND.value
    elif tile == 2:
        return 1 << TileMask.CASTLE.value
    return 0

map_formatted = [[map_tile_to_bitmask(x) for x in row] for row in mapdata['game_map']]

# %%
counter = 0
craftsman_strid_to_intid = {}
craftsmen_formatted = []
for c in mapdata['craftsmen']['team1']:
    new_craftsman = Craftsman(counter, c['x'], c['y'], True)
    craftsmen_formatted.append(new_craftsman)
    craftsman_strid_to_intid[c['id']] = counter
    counter += 1
for c in mapdata['craftsmen']['team2']:
    new_craftsman = Craftsman(counter, c['x'], c['y'], False)
    craftsmen_formatted.append(new_craftsman)
    craftsman_strid_to_intid[c['id']] = counter
    counter += 1

print(craftsman_strid_to_intid)

# %%
actiontxt = open(action_path, "r").read()

# Split the input string based on "- -"
turns = actiontxt.strip().split("- -")


# Remove empty strings from the list
turns = [section.strip() for section in turns]
print (turns)

# Convert each section to an array of arrays
actions = [[action.split(' ') for action in (turn.split('\n') if turn else [])] for turn in turns]

idxToActionEnum = [
    [ActionType.MOVE, SubActionType.MOVE_UP],
    [ActionType.MOVE, SubActionType.MOVE_DOWN],
    [ActionType.MOVE, SubActionType.MOVE_LEFT],
    [ActionType.MOVE, SubActionType.MOVE_RIGHT],
    [ActionType.MOVE, SubActionType.MOVE_UP_LEFT],
    [ActionType.MOVE, SubActionType.MOVE_UP_RIGHT],
    [ActionType.MOVE, SubActionType.MOVE_DOWN_LEFT],
    [ActionType.MOVE, SubActionType.MOVE_DOWN_RIGHT],
    [ActionType.BUILD, SubActionType.BUILD_UP],
    [ActionType.BUILD, SubActionType.BUILD_DOWN],
    [ActionType.BUILD, SubActionType.BUILD_LEFT],
    [ActionType.BUILD, SubActionType.BUILD_RIGHT],
    [ActionType.DESTROY, SubActionType.DESTROY_UP],
    [ActionType.DESTROY, SubActionType.DESTROY_DOWN],
    [ActionType.DESTROY, SubActionType.DESTROY_LEFT],
    [ActionType.DESTROY, SubActionType.DESTROY_RIGHT],
    [ActionType.STAY, SubActionType.STAY],
  ]

actions = [[GameAction(craftsman_strid_to_intid[action[0]], *idxToActionEnum[int(action[1])]) for action in turn] for turn in actions]

# %%
go = GameOptions()
go.mapWidth = mapdata['game_settings']['map_width']
go.mapHeight = mapdata['game_settings']['map_height']
go.maxTurns =  mapdata['game_settings']['max_turn']
go.wallCoeff =  mapdata['score_coefficients']['wall']
go.castleCoeff =   mapdata['score_coefficients']['castle']
go.territoryCoeff =   mapdata['score_coefficients']['territory']

game = Game(
    go,
    map_formatted,
    craftsmen_formatted
)

# %%
for i, turn in enumerate(actions):
    for action in turn:
        game.addAction(action)
    game.nextTurn()
    print(f'Turn {i+2}:',game.getCurrentState().map.calcPoints(game.gameOptions, True), game.getCurrentState().map.calcPoints(game.gameOptions, False))
    # for action in game.getCurrentState().lastTurnActions:
    #     print(action.craftsmanId, action.actionType, action.subActionType)
    print(game.getCurrentState().map.printMap())
    print()


print(game.getCurrentState().map.calcPoints(game.gameOptions, True), game.getCurrentState().map.calcPoints(game.gameOptions, False))