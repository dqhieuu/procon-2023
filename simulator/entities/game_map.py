from entities.tile import Tile


class GameMap:
    def __init__(self):
        self.map: list[list[Tile]] = []

    @property
    def width(self):
        return len(self.map[0])

    @property
    def height(self):
        return len(self.map)

    def is_valid_pos(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x, y):
        return self.map[y][x]

    def set_tile(self, x, y, tile):
        self.map[y][x] = tile
