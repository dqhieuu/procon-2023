extends AspectRatioContainer

@export var width: int
@export var height: int

var turn_number = 1

# Called when the node enters the scene tree for the first time.
func _ready():
	var current_state = await HTTP.get_current_state()
	
	load_map(current_state)
	#load_mock_map(20,15)


func _turn_state_to_string(str):
	var turn_state_map = {
		'initial': "Initial",
		'team1_turn': "Team 1 (Blue team)",
		'team2_turn': "Team 2 (Red team)",
	}
	return turn_state_map.get(str) if turn_state_map.get(str) != null else str

func get_node_by_group(group):
	return get_tree().get_first_node_in_group(group)

func get_nodes_by_group(group):
	return get_tree().get_nodes_in_group(group)

func update_score(score):
	for e in get_nodes_by_group("t1_terr_count"):
		e.text = "Terr count: %d" % score.team1.count.territory
	for e in get_nodes_by_group("t1_castle_count"):
		e.text =  "Castle count: %d" % score.team1.count.castle
	for e in get_nodes_by_group("t1_wall_count"):
		e.text =  "Wall count: %d" % score.team1.count.wall
	for e in get_nodes_by_group("t1_terr_pts"):
		e.text =  "Terr pts: %d" % score.team1.points.territory
	for e in get_nodes_by_group("t1_castle_pts"):
		e.text =  "Castle pts: %d" % score.team1.points.castle
	for e in get_nodes_by_group("t1_wall_pts"):
		e.text =  "Wall pts: %d" % score.team1.points.wall
	for e in get_nodes_by_group("t1_total_pts"):
		e.text =  "Total pts: %d" % score.team1.points.total
	
	for e in get_nodes_by_group("t2_terr_count"):
		e.text =  "Terr count: %d" % score.team2.count.territory
	for e in get_nodes_by_group("t2_castle_count"):
		e.text =  "Castle count: %d" % score.team2.count.castle
	for e in get_nodes_by_group("t2_wall_count"):
		e.text =  "Wall count: %d" % score.team2.count.wall
	for e in get_nodes_by_group("t2_terr_pts"):
		e.text =  "Terr pts: %d" % score.team2.points.territory
	for e in get_nodes_by_group("t2_castle_pts"):
		e.text =  "Castle pts: %d" % score.team2.points.castle
	for e in get_nodes_by_group("t2_wall_pts"):
		e.text =  "Wall pts: %d" % score.team2.points.wall
	for e in get_nodes_by_group("t2_total_pts"):
		e.text =  "Total pts: %d" % score.team2.points.total


func update_actions_to_be_applied(action_list):
	var has_wall_dict = {}
	var has_destroy_dict = {}
	var has_move_dict = {}
	
	for action in action_list:
		var pos_idx = int(action.pos[1]*width+action.pos[0])
		if action.action_type == "move":
			has_move_dict[pos_idx] = true
		elif action.action_type == "build":
			has_wall_dict[pos_idx] = true
		elif action.action_type == "destroy":
			has_destroy_dict[pos_idx] = true
	
	for i in range($GridContainer.get_child_count()):
		var tile = $GridContainer.get_child(i)
		tile.has_to_be_applied_move = has_move_dict.has(i)
		tile.has_to_be_applied_wall = has_wall_dict.has(i)
		tile.has_to_be_applied_destroy = has_destroy_dict.has(i)

func update_time_left(time):
	for e in get_nodes_by_group("time_left"):
		if time != null:
			e.text = "Time left: %d" % time
		else:
			e.text = "Time left: Infinite"

func load_map(json):
	if json.has('score'):
		var score = json.score
		update_score(score)
	
	var time_left = null
	if json.has("game_status"):
		time_left = json.game_status.remaining
		
	update_time_left(time_left)
	
	var game_state = json.state
	
	var map = game_state.map
	width = json.options.map_width
	height = json.options.map_height
	
	turn_number = game_state.turn_number
	
	var num_of_tiles = width*height;
	var is_num_of_tiles_changed = num_of_tiles != $GridContainer.get_child_count()
	
	if is_num_of_tiles_changed:
		for child in $GridContainer.get_children():
			child.free()

	
	$GridContainer.columns = width
	var aspect_ratio = float(width)/height
	self.ratio = aspect_ratio
	
	if game_state.turn_state == "team1_turn":
		Globals.team_turn = Enums.TeamType.TEAM1
	else:
		Globals.team_turn = Enums.TeamType.TEAM2
	
	var MapTile = preload("res://gamemap_tile.tscn")
	
	var craftsmen = game_state.craftsmen
	
	# enum TileMask
	# 	{
	# 		POND,
	# 		CASTLE,
	# 		T1_WALL,
	# 		T2_WALL,
	# 		T1_CRAFTSMAN,
	# 		T2_CRAFTSMAN,
	# 		T1_CLOSE_TERRITORY,
	# 		T2_CLOSE_TERRITORY,
	# 		T1_OPEN_TERRITORY,
	# 		T2_OPEN_TERRITORY,
	# 	};
	
	for i in range(height):
		for j in range(width):
			# change bitmask_tile to int
			var bitmask_tile = int(map[i][j])

			var tile = MapTile.instantiate() if is_num_of_tiles_changed else $GridContainer.get_child(i*width+j)

			tile.has_pond = bitmask_tile & (1 << 0) != 0
			tile.has_castle = bitmask_tile & (1 << 1) != 0
			tile.is_team1_closed_territory = bitmask_tile & (1 << 6) != 0
			tile.is_team2_closed_territory = bitmask_tile & (1 << 7) != 0
			tile.is_team1_open_territory = bitmask_tile & (1 << 8) != 0
			tile.is_team2_open_territory = bitmask_tile & (1 << 9) != 0

			
			tile.wall_team = Enums.TeamType.NEUTRAL
			if bitmask_tile & (1 << 2) != 0:
				tile.wall_team = Enums.TeamType.TEAM1
			elif bitmask_tile & (1 << 3) != 0:
				tile.wall_team = Enums.TeamType.TEAM2

			tile.craftsman_occupied = Enums.TeamType.NEUTRAL
			if bitmask_tile & (1 << 4) != 0:
				tile.craftsman_occupied = Enums.TeamType.TEAM1
			elif bitmask_tile & (1 << 5) != 0:
				tile.craftsman_occupied = Enums.TeamType.TEAM2

			
			if is_num_of_tiles_changed:
				$GridContainer.add_child(tile)
	
	for e in get_nodes_by_group("turn_info"):
		e.text = "Turn %s: %s" % [game_state.turn_number, _turn_state_to_string(game_state.turn_state)]
	

	var replay_node = get_tree().get_first_node_in_group('replay_feature')
	if json.has("winner") && replay_node.replay_turns == null:
		replay_node.load_replay_data(await HTTP.get_match_history())
