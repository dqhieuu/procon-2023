extends Node

var selected_tile = null

func selected_position():
	if selected_tile == null:
		return null
	
	return get_position_from_index(selected_tile)

func get_position_from_index(idx: int):
	var map = get_tree().get_first_node_in_group("map")
	return [idx%map.width,(map.height - (idx/map.width) - 1)]

	
