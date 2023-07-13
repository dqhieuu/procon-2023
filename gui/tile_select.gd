extends TextureRect

@export var is_hovered = false
@export var is_selected = false

func _process(_delta):
	if Globals.is_picking():
		self_modulate = Color(0.7,0,1,1)
	else:
		self_modulate = Color(1.0,0.8,0.2,1)
	
	if is_selected:
		self_modulate.a = 1.0
	elif is_hovered:
		self_modulate.a = 0.7
	else:
		self_modulate.a = 0.0

func _on_aspect_ratio_container_mouse_entered():
	is_hovered = true
	print(get_parent().get_index())
	Globals.hovered_tile = get_parent().get_index()


func _on_aspect_ratio_container_mouse_exited():
	is_hovered = false
	Globals.hovered_tile = null
