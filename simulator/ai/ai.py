from __future__ import annotations

from enum import Enum
from typing import List

import numpy as np

from entities.craftsman import Craftsman, CraftsmanCommand
from entities.game_map import GameMap
from queue import PriorityQueue

from entities.utils.enums import Team, ActionType, get_direction_from_vector
from game import Game


class CurrentStrategy(Enum):
    CAPTURE_CASTLE = 1
    SABOTAGE_OPPONENT = 2
    EXPAND_TERRITORY = 3
    PASSIVE_AGRESSIVE = 4


class CraftsmanAgent:
    def __init__(self, craftsman: Craftsman, game: Game, critic: CentralizedCritic):
        self.craftsman = craftsman
        self.game = game
        self.current_strategy = CurrentStrategy.CAPTURE_CASTLE
        self.critic = critic

    def get_move(self) -> List[tuple[int, int]]:
        if self.current_strategy == CurrentStrategy.CAPTURE_CASTLE:
            return self.get_capture_castle_move()

    def get_capture_castle_move(self) -> List[tuple[int, int]]:
        map = self.game.current_state.map

        castle_positions = map.get_castle_positions()
        if len(castle_positions) == 0:
            return []

        move_costs = dijkstra(self.craftsman, map, pathOnlyNextMove=True)
        castle_costs = [(move_costs[y][x]['move_cost'], (x, y)) for x, y in castle_positions]
        castle_costs.sort(key=lambda x: x[0])
        if castle_costs[0][0] > 1e10:
            return []

        return move_costs[castle_costs[0][1][1]][castle_costs[0][1][0]]['move_path']


class CentralizedCritic:
    def __init__(self, team: Team, game: Game):
        self.team = team
        self.team_agents = []
        self.game = game

    def act(self):
        for agent in self.team_agents:
            move = agent.get_move()
            if len(move) > 0:
                self.game.add_command(CraftsmanCommand(craftsman_pos=agent.craftsman.pos, action_type=ActionType.MOVE
                                              , direction=get_direction_from_vector((move[0][0] - agent.craftsman.pos[0], move[0][1] - agent.craftsman.pos[1]))))


def dijkstra(craftsman: Craftsman, map: GameMap, pathOnlyNextMove=False) -> np.ndarray:
    res = np.empty_like(map.map, dtype=object)
    for y in range(map.height):
        for x in range(map.width):
            res[y][x] = {'move_cost': 1e20, 'move_path': []}

    team = craftsman.team

    # Move cost
    q = PriorityQueue()
    q.put((0, craftsman.pos, []))
    visited = set()

    while not q.empty():
        cost, pos, path = q.get()
        if pos in visited:
            continue

        visited.add(pos)
        x, y = pos
        res[y][x]['move_cost'] = cost
        res[y][x]['move_path'] = path

        # print(f'cost: {cost}, pos: {pos}, path: {path}')

        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (0, 1), (-1, 0), (0, -1)]:
            nx, ny = x + dx, y + dy
            if not map.is_valid_pos(nx, ny):
                continue
            tile = map.get_tile(nx, ny)
            if tile.has_pond:
                res[ny][nx]['move_cost'] = 1e20
                continue

            local_cost = 1
            if (tile.wall is team.TEAM1 and team is team.TEAM2) or (tile.wall is team.TEAM2 and team is team.TEAM1):
                if (dx, dy) in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    local_cost += 1
                else:
                    local_cost += 2.5
            if len(path) >= 1 and pathOnlyNextMove:
                q.put((cost + local_cost, (nx, ny), path))
            else:
                q.put((cost + local_cost, (nx, ny), [*path, (nx, ny)]))
    return res
