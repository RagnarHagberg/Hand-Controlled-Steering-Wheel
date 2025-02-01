extends Node3D

var rotation_radians = 0


func _on_server_rotation_changed(rotation_data) -> void:
	rotation_radians = (rotation_data["rotation_angle"])
	
	get_node("Wheel").rotation.x = -(rotation_radians - 3.14/2)
