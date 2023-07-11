extends VBoxContainer

var craftsman_id = null
var craftsman_pos = null
var strategy = null
var detail = null


func _process(delta):
	pass


func _on_mouse_entered():
	if craftsman_pos == null:
		Globals.hovered_strategy_craftsman_tile_index = null
		return
	
	print(craftsman_pos)
	
	Globals.hovered_strategy_craftsman_tile_index = Globals.get_index_from_position(craftsman_pos)


func _on_mouse_exited():
	Globals.hovered_strategy_craftsman_tile_index = null
