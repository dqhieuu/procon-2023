extends Node

var _timer = null

var is_using = false

var last_since_used = Time.get_ticks_msec()

func _ready():
	_timer = Timer.new()
	add_child(_timer)

	_timer.connect("timeout", _on_Timer_timeout)
	_timer.set_wait_time(0.4)
	_timer.set_one_shot(false) # Make sure it loops
	_timer.start()



func _on_Timer_timeout():
	if is_using:
		var now = Time.get_ticks_msec()
		if now - last_since_used > 2000:
			is_using = false

	if is_using: return
	
	is_using = true;
	last_since_used = Time.get_ticks_msec()
	
	var current_state = await HTTP.get_current_state()
	
	var map_node = get_tree().get_first_node_in_group('map')
	
	# in replay mode, do not auto fetch map 
	var replay_node = get_tree().get_first_node_in_group('replay_feature')
	if replay_node.replay_turns != null:
		return
	
	# var agent_list_node = get_tree().get_first_node_in_group('agent_list')
	# agent_list_node.update_agent_list(current_state.agent_strategy_list)
	
	var builder_list_node = get_tree().get_first_node_in_group('builder_agent_list')
	builder_list_node.update_agent_list(current_state.state.craftsmen)
	
	if map_node.turn_number != current_state.state.turn_number:
		map_node.load_map(current_state)
	else:
		var time_left = null
		if current_state.has("game_status"):
			time_left = current_state.game_status.remaining
		
		map_node.update_time_left(time_left)
		
		map_node.update_actions_to_be_applied(current_state.actions_to_be_applied)
	
	map_node.update_builder_walls_to_be_applied(current_state.builder_pos_by_craftsman)
	
	is_using = false
