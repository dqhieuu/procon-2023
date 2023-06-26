extends Button

func _input(event):
	if event.is_action_pressed("end_turn"):
		_pressed()


func _pressed():
	Globals.selected_tile = null
	send_command()

func send_command():
	await HTTP.end_turn()
	var current_state = await HTTP.get_current_state()
	
	get_tree().get_first_node_in_group('map').load_map(current_state)
