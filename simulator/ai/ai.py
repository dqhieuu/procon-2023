from __future__ import annotations

from enum import Enum
from queue import PriorityQueue

import numpy as np
from typing import List, Optional

from entities.craftsman import Craftsman, CraftsmanCommand
from entities.game_map import GameMap
from entities.utils.enums import Team, ActionType, get_direction_from_vector
from game import Game


class CurrentStrategy(Enum):
    CAPTURE_CASTLE = 1
    SABOTAGE_OPPONENT = 2
    EXPAND_TERRITORY = 3
    PASSIVE_AGRESSIVE = 4


class CraftsmanAgent:
    def __init__(self, craftsman_id: str, game: Game, critic: CentralizedCritic):
        self.craftsman_id = craftsman_id
        self.game = game
        self.current_strategy = CurrentStrategy.CAPTURE_CASTLE
        self.critic = critic
        self.selected_castle_pos = None

        self.expand_strategy_matrix = []
        self.expand_strategy_position = '00.'

        self.init_esm()

    def init_esm(self):
        file_path = "assets//path_strat_expand.txt"
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line:
                    row = line.split(" ")
                    self.expand_strategy_matrix.append(row)
        self.expand_strategy_matrix = np.array(self.expand_strategy_matrix)

    def get_action(self, other_agents_moved_mask: np.ndarray) -> CraftsmanCommand:
        if self.current_strategy == CurrentStrategy.CAPTURE_CASTLE:
            return self.get_capture_castle_action(other_agents_moved_mask)
        if self.current_strategy == CurrentStrategy.EXPAND_TERRITORY:
            return self.get_expand_territory_action(other_agents_moved_mask)

    @property
    def craftsman(self):
        return self.game.find_craftsman_by_id(self.craftsman_id)

    def get_expand_territory_action(self, other_agent_moved_mask: np.ndarray) -> CraftsmanCommand:
        craftsman = self.craftsman
        current_positions = np.where(self.expand_strategy_matrix == self.expand_strategy_position)
        current_position = (current_positions[0][0], current_positions[1][0])
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        for dx, dy in directions:
            nx, ny = current_position[1] + dx, current_position[0] + dy
            if nx < 0 or ny < 0 or nx >= self.expand_strategy_matrix.shape[1] or ny >= \
                    self.expand_strategy_matrix.shape[0]:
                continue

            if self.expand_strategy_matrix[ny][nx] == '..x':
                self.expand_strategy_matrix[ny][nx] = 'done'
                return CraftsmanCommand(
                    craftsman_pos=craftsman.pos,
                    action_type=ActionType.BUILD,
                    direction=get_direction_from_vector((dx, dy))
                )

        diagonal_directions = [(1, -1), (1, 1), (-1, 1), (-1, -1)]
        candidate_points = []
        for dx, dy in diagonal_directions:
            nx, ny = current_position[1] + dx, current_position[0] + dy
            if nx < 0 or ny < 0 or nx >= self.expand_strategy_matrix.shape[1] or ny >= \
                    self.expand_strategy_matrix.shape[0]:
                continue

            value = self.expand_strategy_matrix[ny][nx]
            if len(value) == 3 and value[0:2].isdigit() and value[2] == '.':
                candidate_points.append((nx, ny))

        if candidate_points:
            min_value = float('inf')
            min_point = None

            for point in candidate_points:
                value = int(self.expand_strategy_matrix[point[1]][point[0]][0:2])
                if value < min_value:
                    min_value = value
                    min_point = point
            self.expand_strategy_position = self.expand_strategy_matrix[min_point[1]][min_point[0]]
            direction = (min_point[0] - current_position[1], min_point[1] - current_position[0])

            return CraftsmanCommand(
                craftsman_pos=craftsman.pos,
                action_type=ActionType.MOVE,
                direction=get_direction_from_vector(direction)
            )

    def get_capture_castle_action(self, other_agent_moved_mask: np.ndarray) -> CraftsmanCommand:
        craftsman = self.craftsman
        map = self.game.current_state.map

        castle_positions = map.get_castle_positions()
        if len(castle_positions) == 0:
            return CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.STAY)

        move_costs = dijkstra(craftsman, map,
                              save_only_one_next_move_in_path=True,
                              all_craftsmen=self.game.current_state.craftsmen,
                              excluded_move_mask=other_agent_moved_mask)
        castle_costs = [(move_costs[y][x]['move_cost'], (x, y)) for x, y in castle_positions]
        castle_costs.sort(key=lambda x: x[0])
        if castle_costs[0][0] > 1e10:
            return CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.STAY)

        return move_costs[castle_costs[0][1][1]][castle_costs[0][1][0]]['move_path']


class CentralizedCritic:
    def __init__(self, team: Team, game: Game):
        self.team = team
        self.team_agents: List[CraftsmanAgent] = []
        self.game = game

    def act(self):
        moved_mask = np.zeros((self.game.current_state.map.height, self.game.current_state.map.width), dtype=bool)
        for agent in self.team_agents:
            moves = agent.get_action(other_agents_moved_mask=moved_mask)
            best_move = moves[0] if len(moves) > 0 else None
            # print(self.team,self.game.current_state.turn_number, agent.craftsman.pos, moves, get_direction_from_vector(
            #             (best_move[0] - agent.craftsman.pos[0], best_move[1] - agent.craftsman.pos[1])))
            if best_move is not None:
                self.game.add_command(CraftsmanCommand(craftsman_pos=agent.craftsman.pos, action_type=ActionType.MOVE
                                                       , direction=get_direction_from_vector(
                        (best_move[0] - agent.craftsman.pos[0], best_move[1] - agent.craftsman.pos[1]))))
                moved_mask[best_move[1]][best_move[0]] = True


def dijkstra(craftsman: Craftsman,
             game_map: GameMap,
             save_only_one_next_move_in_path=False,
             all_craftsmen: Optional[List[Craftsman]] = None,
             excluded_move_mask: Optional[np.ndarray] = None
             ) -> np.ndarray:
    res = np.empty_like(game_map.map, dtype=object)
    for y in range(game_map.height):
        for x in range(game_map.width):
            res[y][x] = {'move_cost': 1e20, 'move_path': []}

    team = craftsman.team

    # Move cost
    q = PriorityQueue()
    q.put((0, craftsman.pos, []))
    visited = set()

    craftsman_pos_dict = None
    if all_craftsmen is not None:
        craftsman_pos_dict = {craftsman.pos: craftsman for craftsman in all_craftsmen}

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
            if not game_map.is_valid_pos(nx, ny):
                continue

            tile = game_map.get_tile(nx, ny)
            if tile.has_pond:
                res[ny][nx]['move_cost'] = 1e20
                continue

            if excluded_move_mask is not None and excluded_move_mask[ny][nx]:
                res[ny][nx]['move_cost'] = 1e20
                continue

            if craftsman_pos_dict is not None and (nx, ny) in craftsman_pos_dict:
                res[ny][nx]['move_cost'] = 1e20
                continue

            local_cost = 1
            if (tile.wall is team.TEAM1 and team is team.TEAM2) or (tile.wall is team.TEAM2 and team is team.TEAM1):
                if (dx, dy) in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    local_cost += 1
                else:
                    local_cost += 1e20
            if len(path) >= 1 and save_only_one_next_move_in_path:
                q.put((cost + local_cost, (nx, ny), path))
            else:
                q.put((cost + local_cost, (nx, ny), [*path, (nx, ny)]))
    return res
