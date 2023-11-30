from entities.utils.enums import TileType, TerritoryType, Team


class Tile:
    def __init__(self):
        self.has_castle = False
        self.has_pond = False
        self.wall = Team.NEUTRAL
        # lazily updated
        self.t1c = False
        self.t2c = False
        self.t1o = False
        self.t2o = False

    @classmethod
    def from_file_string(cls, tile_type: str):
        tile = cls()
        if tile_type == "1":
            tile.has_pond = True
        elif tile_type == "2":
            tile.has_castle = True
        return tile
