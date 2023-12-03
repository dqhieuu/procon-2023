extends Node

const SERVER_PATH = "http://127.0.0.1:3010"

func get_current_state():
	return await _get_request("%s/current_state" % SERVER_PATH)

func end_turn():
	return await _post_request_no_body("%s/end_turn" % SERVER_PATH)

#class CraftsmanCommand(BaseModel):
#    craftsman_pos: tuple[int, int]
#    action_type: ActionType
#    direction: Direction | None = None
func send_command(command):
	return await _post_request("%s/command" % SERVER_PATH, command)

func update_strategy(command):
	return await _post_request("%s/ai_strategy" % SERVER_PATH, command)
	
func get_match_history():
	return await _get_request("%s/history" % SERVER_PATH)
	
func update_builder_pos(command):
	return await _post_request("%s/builder" % SERVER_PATH, command)
	

func _get_request(url: String):
	var HTTP = HTTPRequest.new()
	HTTP.timeout = 5.0 # seconds
	add_child(HTTP)
	var error = HTTP.request(url)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
	var res = await HTTP.request_completed
	remove_child(HTTP)
	return _parse_response(res)
	
func _post_request_no_body(url: String):
	var HTTP = HTTPRequest.new()
	HTTP.timeout = 5.0 # seconds
	add_child(HTTP)
	var error = HTTP.request(url, [], HTTPClient.METHOD_POST)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
	var res = await HTTP.request_completed
	remove_child(HTTP)
	return _parse_response(res)

func _post_request(url: String, payload: Dictionary):
	var HTTP = HTTPRequest.new()
	HTTP.timeout = 5.0 # seconds
	add_child(HTTP)
	var body = JSON.stringify(payload)
	var error = HTTP.request(url, [], HTTPClient.METHOD_POST, body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
	var res = await HTTP.request_completed
	remove_child(HTTP)
	return _parse_response(res)
	

func _parse_response(res):
	var body = res[3]
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	return json.get_data()
