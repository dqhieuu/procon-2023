extends TextureRect

@export var is_hovered = false
@export var is_selected = false

func _process(delta):
	if is_selected:
		self.self_modulate.a = 1.0
	elif is_hovered:
		self.self_modulate.a = 0.7
	else:
		self.self_modulate.a = 0.0

func _on_aspect_ratio_container_mouse_entered():
	is_hovered = true


func _on_aspect_ratio_container_mouse_exited():
	is_hovered = false
