extends Node

var websocket := WebSocketPeer.new()
var connected := false

signal rotation_changed


func _ready():
	var err = websocket.connect_to_url("ws://localhost:8765")
	if err != OK:
		print("Failed to connect: %s" % err)

func _process(delta):
	websocket.poll()
	var state = websocket.get_ready_state()

	if state == WebSocketPeer.STATE_OPEN and not connected:
		connected = true
		print("Connected to server")
		websocket.send_text("Hello from Godot!")

	if state == WebSocketPeer.STATE_CLOSING or state == WebSocketPeer.STATE_CLOSED:
		if connected:
			print("Connection closed")
			connected = false

	if websocket.get_available_packet_count() > 0:
		var message = websocket.get_packet().get_string_from_utf8()
		print("Received from server: %s" % message)
		var json = JSON.new()
		var information = json.parse(message)
		
		emit_signal("rotation_changed", json.data)


func _exit_tree():
	if connected:
		websocket.close()
		print("Gracefully closed the connection")


func _on_button_pressed() -> void:
	if connected == true:
		websocket.send_text("I want data")
