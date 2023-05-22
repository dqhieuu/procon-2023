extends AspectRatioContainer


# Called when the node enters the scene tree for the first time.
func _ready():
	load_map(20,15)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	pass

func load_map(width:int, height:int):
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
		if tilerng <= 0.6:
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
	
