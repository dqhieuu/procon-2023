extends PanelContainer

var craftsman_id = null
var craftsman_pos = null
var craftsman_is_t1 = null
var strategy = null
var builder_cost = 0


func _process(delta):
	# Process server output
	if craftsman_id != null and craftsman_pos != null:
		$AgentInfo/AgentId.text = "Agent: %s (x=%d, y=%d)" % [craftsman_id, craftsman_pos[0], craftsman_pos[1]]
	if strategy != null:
		$AgentInfo/Strategy.text = "Strategy: %s" % strategy
	
	var is_selecting_other_craftsman = Globals.selected_buider_craftsman_id != null and craftsman_id != Globals.selected_buider_craftsman_id
	$AgentInfo/HBoxContainer/ActivateBuilderMode.disabled = is_selecting_other_craftsman
	
	$AgentInfo/HBoxContainer/ActivateBuilderMode.text = "Deactivate builder mode" if craftsman_id == Globals.selected_buider_craftsman_id else "Activate builder mode"
	
	$AgentInfo/CostRow/Cost.text = str(builder_cost)
	
	var map_node = get_tree().get_first_node_in_group('map')
	var should_builder_cost_be_warned = builder_cost == 0 or builder_cost + map_node.turn_number > map_node.max_turns
	$AgentInfo/CostRow/Cost.add_theme_color_override("font_color", Color("#d10000") if  should_builder_cost_be_warned else Color.BLACK)
	
	

func _on_mouse_entered():
	if craftsman_pos == null:
		Globals.hovered_strategy_craftsman_tile_index = null
		return
	
	Globals.hovered_strategy_craftsman_tile_index = Globals.get_index_from_position(craftsman_pos)
	Globals.hovered_craftsman_id = craftsman_id


func _on_mouse_exited():
	Globals.hovered_strategy_craftsman_tile_index = null


func _on_activate_builder_mode_pressed():
	if Globals.selected_buider_craftsman_id != null:
		Globals.selected_buider_craftsman_id = null
	else:
		Globals.selected_buider_craftsman_id = craftsman_id



func _on_clear_build_moves_pressed():
	HTTP.update_builder_pos({"action": "unbuild", "id": craftsman_id})
