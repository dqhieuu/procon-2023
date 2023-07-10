extends Node

var _timer = null


func _ready():
	_timer = Timer.new()
	add_child(_timer)

	_timer.connect("timeout", _on_Timer_timeout)
	_timer.set_wait_time(0.3)
	_timer.set_one_shot(false) # Make sure it loops
	_timer.start()


func _on_Timer_timeout():
	var current_state = await HTTP.get_current_state()
	
	var map_node = get_tree().get_first_node_in_group('map')
	
	# in replay mode, do not auto fetch map 
	var replay_node = get_tree().get_first_node_in_group('replay_feature')
	if replay_node.replay_turns != null:
		return
	
	if map_node.turn_number != current_state.state.turn_number:
		map_node.load_map(current_state)
	else:
		var time_left = null
		if current_state.has("game_status"):
			time_left = current_state.game_status.remaining
		
		map_node.update_time_left(time_left)
	