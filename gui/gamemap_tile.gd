extends AspectRatioContainer

@export var wall_team: Enums.TeamType = Enums.TeamType.NEUTRAL
@export var has_pond = false
@export var has_castle = false
@export var craftsman_occupied: Enums.TeamType = Enums.TeamType.NEUTRAL
@export var is_team1_open_territory = false
@export var is_team1_closed_territory = false
@export var is_team2_open_territory = false
@export var is_team2_closed_territory = false
@export var has_to_be_applied_wall = false
@export var has_to_be_applied_destroy = false
@export var has_to_be_applied_move = false

var in_builder_strategy_by_craftsman_ids = {}
var occupied_craftsman_id = null

func _ready():
	update_visible_sprite()


func _process(_delta):
	update_visible_sprite()
	
func update_visible_sprite():
	var tile_index = self.get_index()
	
	$Castle.visible = has_castle
	$Plain.visible = !has_pond
	$Pond.visible = has_pond
	$Wall.visible = wall_team != Enums.TeamType.NEUTRAL
	
	var wall_modulate = Color(1, 0.3 ,0.3) if wall_team == Enums.TeamType.TEAM2 else Color(0.3,0.3,1)
	var team_modulate = Color(1, 0.3 ,0.3) if craftsman_occupied == Enums.TeamType.TEAM2 else Color(0.3,0.3,1)
	
	$Wall/Walltexture.self_modulate = wall_modulate

	$Craftsman.visible = craftsman_occupied != Enums.TeamType.NEUTRAL
	$Craftsman.self_modulate = team_modulate
	
	$Team1ClosedTerritory.visible = is_team1_closed_territory
	$Team1OpenTerritory.visible = is_team1_open_territory
	$Team2ClosedTerritory.visible = is_team2_closed_territory
	$Team2OpenTerritory.visible = is_team2_open_territory
	
	$TileSelect.is_selected = tile_index == Globals.selected_tile
	$Hammer.self_modulate = team_modulate
	
	$MoveAction.visible = has_to_be_applied_move
	$WallAction.visible = has_to_be_applied_wall
	$DestroyAction.visible = has_to_be_applied_destroy
	
	$AgentHighlight.visible = tile_index == Globals.hovered_strategy_craftsman_tile_index
	
	var has_target = false
	var has_pivot = false
	
	if Globals.hovered_strategy_craftsman_tile_index != null or Globals.hovered_tile != null:
		var agent_info_list = get_tree().get_nodes_in_group("agent_info")
		for agent in agent_info_list:
			var craftsman_idx = Globals.get_index_from_position(agent.craftsman_pos)
			if Globals.hovered_strategy_craftsman_tile_index == craftsman_idx or Globals.hovered_tile == craftsman_idx:
				if agent.target_pos != null and Globals.get_index_from_position(agent.target_pos) == tile_index:
					has_target = true
				if agent.pivot_pos != null and Globals.get_index_from_position(agent.pivot_pos) == tile_index:
					has_pivot = true
				break
		
	$Pivot.visible = has_pivot
	$Target.visible = has_target
	
	$BuilderWall.visible = len(in_builder_strategy_by_craftsman_ids) > 0
	
	var should_builder_wall_be_opaque =  \
		in_builder_strategy_by_craftsman_ids.has(Globals.selected_buider_craftsman_id) or \
			(Globals.selected_buider_craftsman_id == null and in_builder_strategy_by_craftsman_ids.has(Globals.hovered_craftsman_id))
	
	$BuilderWall.self_modulate = Color(1,1,1, 1) if should_builder_wall_be_opaque else Color(1,1,1, 0.3)
	
	

func _get_drag_data(pos):
	var is_build_destroy_wall = Input.is_action_pressed("build_destroy_wall")
	
	var preview
	if is_build_destroy_wall:
		preview = $Hammer.duplicate()
		preview.visible = true
	else:
		preview = $Craftsman.duplicate()

	preview.size = $Craftsman.size
	set_drag_preview(preview) 
	

	return {
		"pos": Globals.get_position_from_index(self.get_index()), 
		"action": "build_destroy_wall" if is_build_destroy_wall else "move_craftsman"
	}

func _can_drop_data(pos, data):
	var from_pos = data.pos
	var to_pos = Globals.get_position_from_index(self.get_index())
	var dir = Globals.pos_change_to_direction(from_pos, to_pos)
	if dir == null:
		return false

	if data.action == "build_destroy_wall":
		if dir == Enums.Direction.UP_LEFT or dir == Enums.Direction.UP_RIGHT \
		or dir == Enums.Direction.DOWN_LEFT or dir == Enums.Direction.DOWN_RIGHT:
			return false
		
	return true

func _drop_data(pos, data):
	print(data)
	Globals.flash_green()
	var from_pos = data.pos
	var to_pos = Globals.get_position_from_index(self.get_index())
	
	var dir = Globals.pos_change_to_direction(from_pos, to_pos)
	var dir_str = Globals.direction_enum_to_string(dir)

	if data.action == "build_destroy_wall":
		if wall_team == Enums.TeamType.NEUTRAL:
			HTTP.send_command({"action_type": "build", "direction": dir_str, "craftsman_pos": from_pos})
		else:
			HTTP.send_command({"action_type": "destroy", "direction": dir_str, "craftsman_pos": from_pos})
	elif data.action == "move_craftsman":
		HTTP.send_command({"action_type": "move", "direction": dir_str, "craftsman_pos": from_pos})
	

func _on_gui_input(event):
	var tile_idx = get_index()
	var tile_pos = Globals.get_position_from_index(tile_idx)
	if event.is_action_pressed("click"):
		if Globals.is_builder_picking():
			HTTP.update_builder_pos({"action": "build", "id": Globals.selected_buider_craftsman_id, "pos": tile_pos})
			return
		
		if Globals.is_picking():
			Globals.update_pos_inputs_by_picking(Globals.get_position_from_index(tile_idx))
			return
		
		if craftsman_occupied == Enums.TeamType.NEUTRAL or Globals.team_turn != craftsman_occupied:
			Globals.selected_tile = null
			return

		if Globals.selected_tile == tile_idx:
			Globals.selected_tile = null
		else:
			Globals.selected_tile = tile_idx
	
	if event.is_action_pressed("right_click"):
		if Globals.is_builder_picking():
			HTTP.update_builder_pos({"action": "unbuild", "id": Globals.selected_buider_craftsman_id, "pos": tile_pos})
		elif Globals.hovered_craftsman_id != null:
			HTTP.update_builder_pos({"action": "unbuild", "id": Globals.hovered_craftsman_id})
			
