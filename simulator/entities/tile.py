from entities.utils.enums import TileType, TerritoryType, Team


class Tile:
    def __init__(self):
        self.has_castle = False
        self.has_pond = False
        self.wall = Team.NEUTRAL
        # lazily updated
        self.is_team1_closed_territory = False
        self.is_team2_closed_territory = False
        self.is_team1_open_territory = False
        self.is_team2_open_territory = False

    # def __repr__(self):
    #     return "{}{}:{}:({})".format(self.has_pond, self.has_castle, self.wall.name,
    #                                  ','.join(
    #                                      list(map(lambda
    #                                                   val: 'N' if val == TerritoryType.NEUTRAL else 'C' if val == TerritoryType.CLOSED else 'O',
    #                                               self.is_team_territory))
    #                                  ))

    @classmethod
    def from_file_string(cls, tile_type: str):
        tile = cls()
        if tile_type == "1":
            tile.has_pond = True
        elif tile_type == "2":
            tile.has_castle = True
        return tile
