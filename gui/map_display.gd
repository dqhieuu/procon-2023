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


func update_time_left(time):
	for e in get_nodes_by_group("time_left"):
		if time != null:
			e.text = "Time left: %d" % time
		else:
			e.text = "Time left: Infinite"

func load_map(state):
	if state.has('score'):
		var score = state.score
		update_score(score)
	
	var time_left = null
	if state.has("game_status"):
		time_left = state.game_status.remaining
		
	update_time_left(time_left)
		
	
	var game_state = state.state
	for child in $GridContainer.get_children():
		child.free()
		
	turn_number = game_state.turn_number
	
	var map = game_state.map.map
	width = map[0].size()
	height = map.size()
	
	$GridContainer.columns = width
	var aspect_ratio = float(width)/height
	self.ratio = aspect_ratio

	
	var string_to_team_type = {
		'team1': Enums.TeamType.TEAM1,
		'team2': Enums.TeamType.TEAM2,
		'neutral': Enums.TeamType.NEUTRAL,
	}
	
	if game_state.turn_state == "team1_turn":
		Globals.team_turn = Enums.TeamType.TEAM1
	else:
		Globals.team_turn = Enums.TeamType.TEAM2
	
	var MapTile = preload("res://gamemap_tile.tscn")
	
	var craftsmen = game_state.craftsmen
	
	for i in range(height):
		for j in range(width):
			var json_tile = map[i][j]
			var tile = MapTile.instantiate()
			tile.wall_team = string_to_team_type[json_tile.wall]
			tile.has_pond = json_tile.has_pond
			tile.has_castle = json_tile.has_castle
			tile.is_team1_closed_territory = json_tile.t1c
			tile.is_team2_closed_territory = json_tile.t2c
			tile.is_team1_open_territory = json_tile.t1o
			tile.is_team2_open_territory = json_tile.t2o
			
			$GridContainer.add_child(tile)

	for man in craftsmen:
		var tile = $GridContainer.get_child(man.pos[1]*width+man.pos[0])
		tile.craftsman_occupied = string_to_team_type[man.team]
	
	for e in get_nodes_by_group("turn_info"):
		e.text = "Turn %s: %s" % [game_state.turn_number, _turn_state_to_string(game_state.turn_state)]
	

	var replay_node = get_tree().get_first_node_in_group('replay_feature')
	if state.has("winner") && replay_node.replay_turns == null:
		replay_node.load_replay_data(await HTTP.get_match_history())
