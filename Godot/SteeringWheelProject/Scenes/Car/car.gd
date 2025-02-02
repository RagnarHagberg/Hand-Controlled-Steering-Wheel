extends VehicleBody3D

var horsepower = 3000
var target_speed = 10
var current_effect = 500
var coin_count = 0
# P = f * v
# f = P/v
var steer_limit = deg_to_rad(30)

var input_steering = 0
func _physics_process(delta):
	engine_force = calculate_engine_force()
	
	# Correct rotation if it falls over
	if rotation_degrees.z < -30 or rotation_degrees.z > 30:
		rotation_degrees.z = 0
		
	print("engine_force" + str(engine_force))
	print("linear velocity" + str(linear_velocity))
	print("total velocity" + str(get_velocity()))
func set_input_steering(new_value):
	input_steering = new_value
	
	steering = min(input_steering, steer_limit)

func calculate_engine_force():
	
	
	var v = get_velocity()
	
	if v < target_speed:
		current_effect += 10
	else:
		current_effect -= 10
		
	
	var P = min(current_effect, horsepower)
	var f = P/v
	return f
func get_velocity():
	var total_velocity = ((linear_velocity[0]**2)+(linear_velocity[1]**2)+(linear_velocity[2]**2))**0.5
	
	return total_velocity


func _on_area_3d_area_entered(area: Area3D) -> void:
	if area.get_parent().is_in_group("Coin"):
		area.get_parent().queue_free()
		coin_count += 1
		get_parent().set_coins(coin_count)
