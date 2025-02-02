extends Node3D

var rotation_radians = 0


func _on_server_rotation_changed(rotation_data) -> void:
	rotation_radians = (rotation_data["rotation_angle"])
	var steering_wheel_rotation = -(rotation_radians - 3.14/2)
	get_node("Car/Camera3D/Wheel").rotation.x = (steering_wheel_rotation)
	get_node("Car").set_input_steering(steering_wheel_rotation/10)

func set_coins(new_value):
	get_node("Hud/Label").text = "Coins: " + str(new_value)
