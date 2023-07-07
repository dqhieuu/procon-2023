extends VBoxContainer


var replay_turns = null

func load_replay_data_by_text_input():
	var obj = JSON.parse_string($LoadGroup/TextEdit.text)
	load_replay_data(obj)
	
	
func load_replay_data(dataObj):
	if dataObj == null:
		$LoadGroup/TextEdit.text = ''
		return
	
	replay_turns = dataObj

	$TurnSlider.max_value = replay_turns.size()
	$TurnSlider.tick_count = replay_turns.size()
	get_tree().get_first_node_in_group('map').load_map(replay_turns[0])
	$LoadGroup/TextEdit.text = ''


func _process(delta):
	$TurnSlider.editable = replay_turns != null
	$LoadGroup/LoadHistoryBtn.disabled = $LoadGroup/TextEdit.text.length() <= 0
	


func _on_load_history_btn_pressed():
	load_replay_data_by_text_input()


func _on_turn_slider_value_changed(value):
	get_tree().get_first_node_in_group('map').load_map(replay_turns[$TurnSlider.value - 1])
