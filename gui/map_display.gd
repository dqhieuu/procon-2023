extends AspectRatioContainer

@export var width: int
@export var height: int

# Called when the node enters the scene tree for the first time.
func _ready():
	var current_state = await HTTP.get_current_state()
	
	load_map(current_state)
	#load_mock_map(20,15)


func _turn_state_to_string(str):
	var turn_state_map = {
		'team1_turn': "Team 1 (Red team)",
		'team2_turn': "Team 2 (Blue team)",
	}
	return turn_state_map.get(str) if turn_state_map.get(str) != null else str

func load_map(game_state):
	for child in $GridContainer.get_children():
		child.free()
	
	var map = game_state.map.map
	width = map[0].size()
	height = map.size()
	
	$GridContainer.columns = width
	var aspect_ratio = float(width)/height
	self.ratio = aspect_ratio
	
	var int_to_tile_type = {
		0: Enums.TileType.PLAIN,
		1: Enums.TileType.CASTLE,
		2: Enums.TileType.POND,
	}
	
	var string_to_team_type = {
		'team1': Enums.TeamType.TEAM1,
		'team2': Enums.TeamType.TEAM2,
		'neutral': Enums.TeamType.NEUTRAL,
	}
	
	var MapTile = preload("res://gamemap_tile.tscn")
	
	var craftmen = game_state.craftmen
	
	for i in range(height):
		for j in range(width):
			var json_tile = map[height-i-1][j]
			var tile = MapTile.instantiate()
			tile.wall_team = string_to_team_type[json_tile.wall]
			tile.has_pond = json_tile.has_pond
			tile.has_castle = json_tile.has_castle
			$GridContainer.add_child(tile)

	for man in craftmen:
		var tile = $GridContainer.get_child((height-man.pos[1]-1)*width+man.pos[0])
		tile.craftman_occupied = string_to_team_type[man.team]
	
	get_tree().get_first_node_in_group("turn_info").text = "Turn %s: %s" % [game_state.turn_number, _turn_state_to_string(game_state.turn_state)]


func load_mock_map(width:int, height:int):
	$GridContainer.columns = width
	var aspect_ratio = float(width)/height
	self.ratio = aspect_ratio
	

	var MapTile = preload("res://gamemap_tile.tscn")
	for i in range(width*height):
		var tile = MapTile.instantiate()
		var wallrng = randf()
		if wallrng <= 0.33:
			tile.wall_team = Enums.TeamType.NEUTRAL
		elif wallrng <= 0.67:
			tile.wall_team = Enums.TeamType.TEAM1
		else:
			tile.wall_team = Enums.TeamType.TEAM2
		
		var tilerng = randf()
		if tilerng <= 0.7:
			tile.type = Enums.TileType.PLAIN
		elif tilerng <= 0.9:
			tile.type = Enums.TileType.POND
		else:
			tile.type = Enums.TileType.CASTLE
			
		var teamrng = randf()
		if teamrng <= 0.9:
			tile.craftman_occupied = Enums.TeamType.NEUTRAL
		elif teamrng <= 0.95:
			tile.craftman_occupied = Enums.TeamType.TEAM1
		else:
			tile.craftman_occupied = Enums.TeamType.TEAM2
			
		$GridContainer.add_child(tile)
	
