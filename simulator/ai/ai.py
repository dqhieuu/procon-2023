from __future__ import annotations

from queue import PriorityQueue

import numpy as np
from typing import List, Optional

from ai.ai_request import AIStrategyEnum, AIStrategyRequest
from entities.craftsman import Craftsman, CraftsmanCommand
from entities.game_map import GameMap
from entities.utils.enums import Team, ActionType, get_direction_from_vector, get_direction_vector
from game import Game


class CraftsmanAgent:
    def __init__(self, craftsman_id: str, game: Game, critic: CentralizedCritic):
        self.craftsman_id = craftsman_id
        self.game = game
        self.current_strategy = AIStrategyEnum.MANUAL
        self.critic = critic

        # manual strategy
        self.manual_destination = None

        # expand strategy
        self.expand_strategy_matrix = []
        self.expand_strategy_position = '00.'
        self.expand_pivot_pos = None
        self.init_esm()

        # capture castle strategy
        self.selected_castle_pos = None



    def init_esm(self):
        file_path = "assets//path_strat_expand.txt"
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line:
                    row = line.split(" ")
                    self.expand_strategy_matrix.append(row)
        self.expand_strategy_matrix = np.array(self.expand_strategy_matrix)

    def set_strategy(self, req: AIStrategyRequest):
        self.current_strategy = req.strategy
        if self.current_strategy == AIStrategyEnum.CAPTURE_CASTLE:
            self.selected_castle_pos = req.detail.get("castle_pos", None)
        elif self.current_strategy == AIStrategyEnum.MANUAL:
            self.manual_destination = req.detail.get("destination", None)
        elif self.current_strategy == AIStrategyEnum.EXPAND_TERRITORY:
            # TODO: implement this
            self.expand_pivot_pos = req.detail.get("pivot_pos", None)

    def get_action(self, other_agents_moved_mask: np.ndarray) -> Optional[CraftsmanCommand]:
        if self.current_strategy == AIStrategyEnum.MANUAL:
            return self.get_manual_action(other_agents_moved_mask)
        if self.current_strategy == AIStrategyEnum.CAPTURE_CASTLE:
            return self.get_capture_castle_action(other_agents_moved_mask)
        if self.current_strategy == AIStrategyEnum.EXPAND_TERRITORY:
            return self.get_expand_territory_action(other_agents_moved_mask)


    @property
    def craftsman(self):
        return self.game.find_craftsman_by_id(self.craftsman_id)

    def get_expand_territory_action(self, other_agent_moved_mask: np.ndarray) -> CraftsmanCommand:
        craftsman = self.craftsman
        current_positions = np.where(self.expand_strategy_matrix == self.expand_strategy_position)
        print(current_positions)
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

        map_tiles_insight = dijkstra(craftsman, map,
                              save_only_one_next_move_in_path=True,
                              all_craftsmen=self.game.current_state.craftsmen,
                              excluded_move_mask=other_agent_moved_mask)
        castle_info_list = []
        for x, y in castle_positions:
            castle_info_list.append({
                "cost": map_tiles_insight[y][x]['move_cost'],
                "next_pos_to_move": map_tiles_insight[y][x]['move_path'][0] if len(map_tiles_insight[y][x]['move_path']) > 0 else None,
                "pos": (x, y),
            })

        # Remove castles that are already in our closed territory and castles
        unclosed_territory_castle_info_list = []
        for castle_cost_and_pos in castle_info_list:
            castle_tile = map.get_tile(*castle_cost_and_pos["pos"])
            if not ((castle_tile.t1c and craftsman.team == Team.TEAM1) or (castle_tile.t2c and craftsman.team == Team.TEAM2)):
                unclosed_territory_castle_info_list.append(castle_cost_and_pos)
        castle_info_list = unclosed_territory_castle_info_list

        select_castle_info = None
        # Select the castle that we chose before and is still needed to be captured
        if self.selected_castle_pos is not None and self.selected_castle_pos in castle_positions:
            for elem in castle_info_list:
                if elem == self.selected_castle_pos:
                    select_castle_info = elem
                    break

        # Select the castle that is closest to us
        if select_castle_info is None:
            castle_info_list.sort(key=lambda x: x["cost"])
            select_castle_info = castle_info_list[0]

        # If the castle is too far away, then just stay
        if select_castle_info["cost"] > 1000:
            return CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.STAY)

        cur_pos = craftsman.pos

        # We are already at the castle
        if select_castle_info["cost"] == 0:
            for build_wall_dir_vec in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                tile = map.get_tile(cur_pos[0] + build_wall_dir_vec[0], cur_pos[1] + build_wall_dir_vec[1])
                # If there is an opponent wall, then destroy it
                if (tile.wall == Team.TEAM1 and craftsman.team == Team.TEAM2) or (tile.wall == Team.TEAM2 and craftsman.team == Team.TEAM1):
                    destroy_wall_dir = get_direction_from_vector(build_wall_dir_vec)
                    return CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY, direction=destroy_wall_dir)
                # If there is no wall, then build our wall
                elif tile.wall == Team.NEUTRAL:
                    build_wall_dir = get_direction_from_vector(build_wall_dir_vec)
                    return CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.BUILD, direction=build_wall_dir)


        # If we are not at the castle, then move towards it
        next_pos = select_castle_info["next_pos_to_move"]
        dir_vec = (next_pos[0] - cur_pos[0], next_pos[1] - cur_pos[1])
        direction = get_direction_from_vector(dir_vec)
        tile_at_next_pos = map.get_tile(*next_pos)

        # If there is an opponent wall, then destroy it before moving
        if (tile_at_next_pos.wall == Team.TEAM1 and craftsman.team == Team.TEAM2) or (tile_at_next_pos.wall == Team.TEAM2 and craftsman.team == Team.TEAM1):
            return CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY, direction=direction)

        # If there is no wall, then move towards the castle
        return CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE, direction=direction)

    def get_manual_action(self, other_agent_moved_mask: np.ndarray) -> CraftsmanCommand | None:
        if self.manual_destination is None:
            return None

        craftsman = self.craftsman
        map = self.game.current_state.map

        map_tiles_insight = dijkstra(craftsman, map,
                              save_only_one_next_move_in_path=True,
                              all_craftsmen=self.game.current_state.craftsmen,
                              excluded_move_mask=other_agent_moved_mask)
        destination_insight = map_tiles_insight[self.manual_destination[1]][self.manual_destination[0]]

        # If we are already at the destination, reset the manual destination and do nothing
        if destination_insight['move_cost'] == 0:
            self.manual_destination = None
            return None

        # If the destination is too far away, unable to reach, then do nothing
        if destination_insight['move_cost'] > 1000 or len(destination_insight['move_path']) <= 0:
            return None

        cur_pos = craftsman.pos
        next_pos = destination_insight['move_path'][0]
        dir_vec = (next_pos[0] - cur_pos[0], next_pos[1] - cur_pos[1])
        direction = get_direction_from_vector(dir_vec)
        tile_at_next_pos = map.get_tile(*next_pos)

        # If there is an opponent wall, then destroy it before moving
        if (tile_at_next_pos.wall == Team.TEAM1 and craftsman.team == Team.TEAM2) or (tile_at_next_pos.wall == Team.TEAM2 and craftsman.team == Team.TEAM1):
            return CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.DESTROY, direction=direction)

        # If there is no wall, then move towards the destination
        return CraftsmanCommand(craftsman_pos=craftsman.pos, action_type=ActionType.MOVE, direction=direction)


class CentralizedCritic:
    def __init__(self, team: Team, game: Game):
        self.team = team
        self.team_agents: List[CraftsmanAgent] = []
        self.game = game

    async def act(self):
        from server import do_command
        moved_mask = np.zeros((self.game.current_state.map.height, self.game.current_state.map.width), dtype=bool)
        for agent in self.team_agents:
            action = agent.get_action(other_agents_moved_mask=moved_mask)
            if action is not None:
                if action.action_type == ActionType.MOVE:
                    await do_command(action)
                    dir_vec = get_direction_vector(action.direction)
                    next_pos = (agent.craftsman.pos[0] + dir_vec[0], agent.craftsman.pos[1] + dir_vec[1])
                    if self.game.current_state.map.is_valid_pos(*next_pos):
                        moved_mask[next_pos[1]][next_pos[0]] = True
                elif action.action_type == ActionType.BUILD or action.action_type == ActionType.DESTROY:
                    await do_command(action)

    def update_agent_strategy(self, strategy: AIStrategyRequest):
        for agent in self.team_agents:
            if agent.craftsman.id == strategy.craftsman_id:
                agent.set_strategy(strategy)
                break


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
        # Remove the current craftsman from the dict
        craftsman_pos_dict.pop(craftsman.pos)

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
