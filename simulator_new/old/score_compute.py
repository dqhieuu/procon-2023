from copy import deepcopy

from entities.game_map import GameMap
from entities.score_coeff import ScoreCoefficients
from entities.utils.enums import Team
from utils import timeit



def get_territory_computed_map(prev_turn_map: GameMap, cur_turn_map: GameMap) -> GameMap:
    new_map = deepcopy(cur_turn_map)

    # Reset territory
    for y in range(new_map.height):
        for x in range(new_map.width):
            new_map.get_tile(x, y).t1c = False
            new_map.get_tile(x, y).t2c = False
            new_map.get_tile(x, y).t1o = False
            new_map.get_tile(x, y).t2o = False

    # Make prev turn map's territory open territory
    for y in range(new_map.height):
        for x in range(new_map.width):
            prev_tile_ref = prev_turn_map.get_tile(x, y)
            if prev_tile_ref.t1c or prev_tile_ref.t1o:
                new_map.get_tile(x, y).t1o = True
            if prev_tile_ref.t2c or prev_tile_ref.t2o:
                new_map.get_tile(x, y).t2o = True

    # Delete open territory if there is wall on it
    for y in range(new_map.height):
        for x in range(new_map.width):
            if cur_turn_map.get_tile(x, y).wall != Team.NEUTRAL:
                new_map.get_tile(x, y).t1o = False
                new_map.get_tile(x, y).t2o = False

    # 4 way flood fill to find closed territory
    teams = [Team.TEAM1, Team.TEAM2]
    for team in teams:
        visited = set()
        for y in range(new_map.height):
            for x in range(new_map.width):
                if (x, y) in visited:
                    continue
                if new_map.get_tile(x, y).wall == team:
                    visited.add((x, y))
                    continue
                _flood_fill((x, y), team, new_map, visited)

    return new_map


def _flood_fill(pos: tuple[int, int], team: Team, map: GameMap, visited: set[tuple[int, int]]):
    queue = [pos]
    to_be_filled = []
    enclosed = True
    while len(queue) > 0:
        x, y = queue.pop()
        if not map.is_valid_pos(x, y):
            enclosed = False
            continue
        if (x, y) in visited or map.get_tile(x, y).wall == team:
            continue
        visited.add((x, y))
        to_be_filled.append((x, y))
        queue.append((x + 1, y))
        queue.append((x - 1, y))
        queue.append((x, y + 1))
        queue.append((x, y - 1))
    if not enclosed:
        return

    for x, y in to_be_filled:
        map.get_tile(x, y).t1o = False
        map.get_tile(x, y).t2o = False
        if team == Team.TEAM1:
            map.get_tile(x, y).t1c = True
        else:
            map.get_tile(x, y).t2c = True


def compute_score(map: GameMap, coeff: ScoreCoefficients):
    score = {
        "team1": {
            "count": {
                "territory": 0,
                "wall": 0,
                "castle": 0,
            },
            "points": {
                "territory": 0,
                "wall": 0,
                "castle": 0,
                "total": 0,
            },
        },
        "team2": {
            "count": {
                "territory": 0,
                "wall": 0,
                "castle": 0,
            },
            "points": {
                "territory": 0,
                "wall": 0,
                "castle": 0,
                "total": 0,
            },
        }
    }

    for y in range(map.height):
        for x in range(map.width):
            if map.get_tile(x, y).wall == Team.TEAM1:
                score["team1"]["count"]["wall"] += 1
            elif map.get_tile(x, y).wall == Team.TEAM2:
                score["team2"]["count"]["wall"] += 1
            if map.get_tile(x, y).t1c or map.get_tile(x, y).t1o:
                score["team1"]["count"]["territory"] += 1
            if map.get_tile(x, y).t2c or map.get_tile(x, y).t2o:
                score["team2"]["count"]["territory"] += 1
            if map.get_tile(x, y).has_castle:
                if map.get_tile(x, y).t1o or map.get_tile(x, y).t1c:
                    score["team1"]["count"]["castle"] += 1
                elif map.get_tile(x, y).t2o or map.get_tile(x, y).t2c:
                    score["team2"]["count"]["castle"] += 1

    score["team1"]["points"]["territory"] = score["team1"]["count"]["territory"] * coeff.territory
    score["team1"]["points"]["wall"] = score["team1"]["count"]["wall"] * coeff.wall
    score["team1"]["points"]["castle"] = score["team1"]["count"]["castle"] * coeff.castle
    score["team1"]["points"]["total"] = score["team1"]["points"]["territory"] + score["team1"]["points"]["wall"] + score["team1"]["points"]["castle"]

    score["team2"]["points"]["territory"] = score["team2"]["count"]["territory"] * coeff.territory
    score["team2"]["points"]["wall"] = score["team2"]["count"]["wall"] * coeff.wall
    score["team2"]["points"]["castle"] = score["team2"]["count"]["castle"] * coeff.castle
    score["team2"]["points"]["total"] = score["team2"]["points"]["territory"] + score["team2"]["points"]["wall"] + score["team2"]["points"]["castle"]

    return score


