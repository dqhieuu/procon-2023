from entities.utils.enums import TileType, TerritoryType, Team


class Tile:
    def __init__(self, tile_type: TileType):
        self.type = tile_type
        self.wall = Team.NEUTRAL
        # lazily updated
        self.is_team_territory = [TerritoryType.NEUTRAL, TerritoryType.NEUTRAL]

    def set_wall(self, wall_team: Team) -> bool:
        if type == TileType.CASTLE or type == TileType.POND:
            return False

        if (self.type == TileType.PLAIN and (wall_team == Team.TEAM1 or wall_team == Team.TEAM2)) or \
                ((self.wall == Team.TEAM1 or self.wall == Team.TEAM2) and wall_team == Team.NEUTRAL):
            self.wall = wall_team
            return True

        return False

    def __repr__(self):
        return "{}:{}:({})".format(self.type.name, self.wall.name,
                                   ','.join(
                                       list(map(lambda
                                                    val: 'N' if val == TerritoryType.NEUTRAL else 'C' if val == TerritoryType.CLOSED else 'O',
                                                self.is_team_territory))
                                   ))

    @classmethod
    def from_file_string(cls, tile_type: str):
        return Tile(TileType(int(tile_type)))
