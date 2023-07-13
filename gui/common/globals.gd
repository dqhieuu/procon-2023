extends Node

var selected_tile = null
var hovered_tile = null
var hovered_strategy_craftsman_tile_index = null

var pos_inputs_to_be_updated = null

var team_turn: Enums.TeamType

func is_picking():
	return pos_inputs_to_be_updated != null && len(pos_inputs_to_be_updated) == 2

func update_pos_inputs_by_picking(pos):
	pos_inputs_to_be_updated[0].value = pos[0]
	pos_inputs_to_be_updated[1].value = pos[1]
	
	pos_inputs_to_be_updated = null

func selected_position():
	if selected_tile == null:
		return null
	
	return get_position_from_index(selected_tile)

func get_position_from_index(idx: int):
	var map = get_tree().get_first_node_in_group("map")
	return [idx%map.width,idx/map.width]

func get_index_from_position(position):
	var map = get_tree().get_first_node_in_group("map")
	return position[0]+position[1]*map.width

func flash_green():
	var animation = get_tree().get_first_node_in_group("animation")
	animation.play("flash_green")

func pos_change_to_direction(fromPos, toPos):
	var dx = toPos[0] - fromPos[0]
	var dy = toPos[1] - fromPos[1]
	if abs(dx) > 1 or abs(dy) > 1:
		return null
	
	if dx == -1 and dy == -1:
		return Enums.Direction.UP_LEFT
	if dx == -1 and dy == 0:
		return Enums.Direction.LEFT
	if dx == -1 and dy == 1:
		return Enums.Direction.DOWN_LEFT
	if dx == 0 and dy == -1:
		return Enums.Direction.UP
	if dx == 0 and dy == 1:
		return Enums.Direction.DOWN
	if dx == 1 and dy == -1:
		return Enums.Direction.UP_RIGHT
	if dx == 1 and dy == 0:
		return Enums.Direction.RIGHT
	if dx == 1 and dy == 1:
		return Enums.Direction.DOWN_RIGHT
	
func direction_enum_to_string(dir):
	if dir == null:
		return null
	var map = {
		Enums.Direction.UP: 'up',
		Enums.Direction.DOWN: 'down',
		Enums.Direction.LEFT: 'left',
		Enums.Direction.RIGHT: 'right',
		Enums.Direction.UP_LEFT: 'up_left',
		Enums.Direction.UP_RIGHT: 'up_right',
		Enums.Direction.DOWN_LEFT: 'down_left',
		Enums.Direction.DOWN_RIGHT: 'down_right',
	}
	return map[dir]
