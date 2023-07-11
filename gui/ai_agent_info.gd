extends VBoxContainer

var craftsman_id = 25
var tile_index = 25


func _ready():
	pass # Replace with function body.



func _process(delta):
	pass


func _on_mouse_entered():
	Globals.hovered_strategy_craftsman_tile_index = tile_index


func _on_mouse_exited():
	Globals.hovered_strategy_craftsman_tile_index = null
