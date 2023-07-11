extends VBoxContainer

var craftsman_id = null
var craftsman_pos = null
var strategy = null
var strategy_detail = null

var target_pos = null


func _process(delta):
	# Process server output
	var new_target_pos = null
	if craftsman_id != null and craftsman_pos != null:
		$AgentId.text = "Agent: %s (x=%d, y=%d)" % [craftsman_id, craftsman_pos[0], craftsman_pos[1]]
	if strategy != null:
		$Strategy.text = "Strategy: %s" % strategy
	if strategy_detail != null:
		if strategy == "manual":
			if strategy_detail.destination == null:
				$StrategyDetail.text = "No destination set"
			else:
				$StrategyDetail.text = "Going to pos: x=%d, y=%d" % [strategy_detail.destination[0], strategy_detail.destination[1]]
				new_target_pos = strategy_detail.destination
		elif strategy == "capture_castle":
			if strategy_detail.castle_pos == null:
				$StrategyDetail.text = "Going to nearest castle"
			else:
				$StrategyDetail.text = "Going to castle pos: x=%d, y=%d" % [strategy_detail.castle_pos[0], strategy_detail.castle_pos[1]]
				new_target_pos = strategy_detail.castle_pos
		elif strategy == "expand_territory":
			$StrategyDetail.text = "Expanding territory (set wrong)"
	target_pos = new_target_pos

func _on_mouse_entered():
	if craftsman_pos == null:
		Globals.hovered_strategy_craftsman_tile_index = null
		return
	
	Globals.hovered_strategy_craftsman_tile_index = Globals.get_index_from_position(craftsman_pos)


func _on_mouse_exited():
	Globals.hovered_strategy_craftsman_tile_index = null


func _on_pick_destination_pressed():
	Globals.selected_tile = null
	Globals.pos_inputs_to_be_updated = [$StrategySelector/Man/PositionControl/X, $StrategySelector/Man/PositionControl/Y]


func _on_pick_expand_pivot_pressed():
	Globals.selected_tile = null
	Globals.pos_inputs_to_be_updated = [$StrategySelector/Terr/PivotPosition/X, $StrategySelector/Terr/PivotPosition/Y]


func _on_pick_castle_pressed():
	Globals.selected_tile = null
	Globals.pos_inputs_to_be_updated = [$StrategySelector/Cast/PositionControl/X, $StrategySelector/Cast/PositionControl/Y]


func _on_go_to_input_dest_pressed():
	var dest_x = $StrategySelector/Man/PositionControl/X.value
	var dest_y = $StrategySelector/Man/PositionControl/Y.value
	HTTP.update_strategy({'craftsman_id': craftsman_id, "strategy": 'manual', "detail":{'destination':[dest_x, dest_y]}})


func _on_full_manual_pressed():
	HTTP.update_strategy({'craftsman_id': craftsman_id, "strategy": 'manual', "detail":{}})



func _on_capture_castle_from_pos_btn_pressed():
	var castle_x = $StrategySelector/Cast/PositionControl/X.value
	var castle_y = $StrategySelector/Cast/PositionControl/Y.value
	HTTP.update_strategy({'craftsman_id': craftsman_id, "strategy": 'capture_castle', "detail":{'castle_pos':[castle_x, castle_y]}})


func _on_capture_nearest_castles_btn_pressed():
	HTTP.update_strategy({'craftsman_id': craftsman_id, "strategy": 'capture_castle', "detail":{}})
	

