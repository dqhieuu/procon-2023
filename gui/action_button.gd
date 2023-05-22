extends Button


@export var action_type: String
@export var direction: String

func _process(_delta):
	self.disabled = Globals.selected_tile == null

func _pressed():
	send_command()

func send_command():
	if action_type == 'stay':
		HTTP.send_command({"action_type": action_type, "craftman_pos": Globals.selected_position()})
	else: 
		HTTP.send_command({"action_type": action_type, "direction": direction, "craftman_pos": Globals.selected_position()})
