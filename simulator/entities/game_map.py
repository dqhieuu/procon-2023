import numpy as np

from entities.tile import Tile


class GameMap:
    def __init__(self):
        self.map: np.ndarray = None

    @property
    def width(self):
        return self.map.shape[1]

    @property
    def height(self):
        return self.map.shape[0]

    def is_valid_pos(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x, y) -> Tile:
        return self.map[y][x]

    def set_tile(self, x, y, tile):
        self.map[y][x] = tile


class ScoreCoefficients:
    def __init__(self, territory: int, wall: int, castle: int):
        self.territory = territory
        self.wall = wall
        self.castle = castle
