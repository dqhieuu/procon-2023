extends VBoxContainer

var agent_list = []

var AgentInfo = preload("res://ai_agent_info.tscn")

func update_agent_list(new_agent_list):
	var is_dirty_agent_list = false
	
	if len(agent_list) != len(new_agent_list):
		is_dirty_agent_list = true
	else:
		for i in range(len(new_agent_list)):
			if agent_list[i].craftsman_id != new_agent_list[i].craftsman_id:
				is_dirty_agent_list = true
				break
	
	agent_list = new_agent_list
		
	if is_dirty_agent_list:
		for child in get_children():
			child.free()
		for agent in agent_list:
			var agent_info_node = AgentInfo.instantiate()
			agent_info_node.craftsman_id = agent.craftsman_id
			add_child(agent_info_node)
		
	var node_list = get_children()
	for i in len(node_list):
		node_list[i].craftsman_pos = agent_list[i].craftsman_pos
		node_list[i].strategy = agent_list[i].strategy
		node_list[i].strategy_detail = agent_list[i].detail
	


func _process(delta):
	pass
