extends AspectRatioContainer

@export var wall_team: Enums.TeamType = Enums.TeamType.NEUTRAL
@export var type: Enums.TileType = Enums.TileType.PLAIN
@export var craftman_occupied: Enums.TeamType = Enums.TeamType.NEUTRAL

# Called when the node enters the scene tree for the first time.
func _ready():
	update_visible_sprite()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta):
	update_visible_sprite()
	
func update_visible_sprite():
	$Castle.visible = type == Enums.TileType.CASTLE
	$Plain.visible = type == Enums.TileType.PLAIN
	$Pond.visible = type == Enums.TileType.POND
	$Wall.visible = wall_team != Enums.TeamType.NEUTRAL
	$Wall/Walltexture.self_modulate = Color(1, 0.3 ,0.3) if wall_team == Enums.TeamType.TEAM1 else Color(0.3,0.3,1)
	$Craftman.visible =  craftman_occupied != Enums.TeamType.NEUTRAL
	$Craftman.self_modulate = Color(1, 0.3 ,0.3) if craftman_occupied == Enums.TeamType.TEAM1 else Color(0.3,0.3,1)
	$TileSelect.is_selected = self.get_index() == Globals.selected_tile


func _on_gui_input(event):
	if event.is_action_pressed("click"):
		if craftman_occupied == Enums.TeamType.NEUTRAL:
			Globals.selected_tile = null
			return

		if Globals.selected_tile == self.get_index():
			Globals.selected_tile = null
		else:
			Globals.selected_tile = self.get_index()
			
