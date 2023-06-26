extends Button

func _input(event):
	if event.is_action_pressed("reset_turn"):
		_pressed()

func _pressed():
	Globals.selected_tile = null
	send_command()

func send_command():
	var all_map_tiles = get_tree().get_first_node_in_group('map').get_child(0).get_children()
	for tile in all_map_tiles:
		if tile.craftsman_occupied != Enums.TeamType.NEUTRAL:
			HTTP.send_command({'action_type': 'stay', "craftsman_pos": Globals.get_position_from_index(tile.get_index())})
