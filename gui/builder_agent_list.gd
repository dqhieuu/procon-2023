extends VBoxContainer

var agent_list = []

var BuilderInfo = preload("res://builder_agent_info.tscn")

func _input(event):
	if event.is_action_pressed("cancel"):
		Globals.selected_buider_craftsman_id = null
	
	if event.is_action_pressed("toggle_builder_mode"):
		if Globals.hovered_craftsman_id == null or Globals.hovered_craftsman_id == Globals.selected_buider_craftsman_id:
			Globals.selected_buider_craftsman_id = null
		else:
			Globals.selected_buider_craftsman_id = Globals.hovered_craftsman_id

	if event.is_action_pressed("generate_builder_pos"):
		send_generate_builder_pos_request()

func update_agent_list(new_agent_list):
	var is_dirty_agent_list = false
	
	if len(agent_list) != len(new_agent_list):
		is_dirty_agent_list = true
	else:
		for i in range(len(new_agent_list)):
			if agent_list[i].id != new_agent_list[i].id:
				is_dirty_agent_list = true
				break
	
	agent_list = new_agent_list
		
	if is_dirty_agent_list:
		for child in get_children():
			child.free()
		for agent in agent_list:
			var builder_info_node = BuilderInfo.instantiate()
			builder_info_node.craftsman_id = agent.id
			add_child(builder_info_node)
		
	var node_list = get_children()
	for i in len(node_list):
		node_list[i].craftsman_pos = agent_list[i].pos

func send_generate_builder_pos_request():
	HTTP.generate_builder_pos()
