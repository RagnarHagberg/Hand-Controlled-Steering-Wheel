extends VehicleBody3D

var horsepower = 100

var steer_limit = deg_to_rad(30)

var input_steering = 0
func _physics_process(delta):
	engine_force = horsepower

func set_input_steering(new_value):
	input_steering = new_value
	steering = min(input_steering, steer_limit)
