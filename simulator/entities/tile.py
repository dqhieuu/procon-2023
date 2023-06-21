from entities.utils.enums import TileType, TerritoryType, Team


class Tile:
    def __init__(self):
        self.has_castle = False
        self.has_pond = False
        self.wall = Team.NEUTRAL
        # lazily updated
        self.is_team_territory = [TerritoryType.NEUTRAL, TerritoryType.NEUTRAL]

    # def set_wall(self, wall_team: Team) -> bool:
    #     if type == TileType.CASTLE or type == TileType.POND:
    #         return False
    #
    #     if (self.type == TileType.PLAIN and (wall_team == Team.TEAM1 or wall_team == Team.TEAM2)) or \
    #             ((self.wall == Team.TEAM1 or self.wall == Team.TEAM2) and wall_team == Team.NEUTRAL):
    #         self.wall = wall_team
    #         return True
    #
    #     return False

    def __repr__(self):
        return "{}{}:{}:({})".format(self.has_pond, self.has_castle, self.wall.name,
                                     ','.join(
                                         list(map(lambda
                                                      val: 'N' if val == TerritoryType.NEUTRAL else 'C' if val == TerritoryType.CLOSED else 'O',
                                                  self.is_team_territory))
                                     ))

    @classmethod
    def from_file_string(cls, tile_type: str):
        tile = cls()
        if tile_type == "1":
            tile.has_pond = True
        elif tile_type == "2":
            tile.has_castle = True
        elif tile_type == "3":
            tile.has_pond = True
            tile.has_castle = True
        return tile
