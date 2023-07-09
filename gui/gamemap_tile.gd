extends AspectRatioContainer

@export var wall_team: Enums.TeamType = Enums.TeamType.NEUTRAL
@export var has_pond = false
@export var has_castle = false
@export var craftsman_occupied: Enums.TeamType = Enums.TeamType.NEUTRAL
@export var is_team1_open_territory = false
@export var is_team1_closed_territory = false
@export var is_team2_open_territory = false
@export var is_team2_closed_territory = false

func _ready():
	update_visible_sprite()


func _process(_delta):
	update_visible_sprite()
	
func update_visible_sprite():
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
	
	$TileSelect.is_selected = self.get_index() == Globals.selected_tile
	$Hammer.self_modulate = team_modulate

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
	if event.is_action_pressed("click"):
		if craftsman_occupied == Enums.TeamType.NEUTRAL or Globals.team_turn != craftsman_occupied:
			Globals.selected_tile = null
			return

		if Globals.selected_tile == self.get_index():
			Globals.selected_tile = null
		else:
			Globals.selected_tile = self.get_index()
			
