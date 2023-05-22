extends Button


func _pressed():
	Globals.selected_tile = null
	send_command()

func send_command():
	var all_map_tiles = get_tree().get_first_node_in_group('map').get_child(0).get_children()
	for tile in all_map_tiles:
		if tile.craftman_occupied != Enums.TeamType.NEUTRAL:
			HTTP.send_command({'action_type': 'stay', "craftman_pos": Globals.get_position_from_index(tile.get_index())})
