extends Node2D
# ============================================================
# Main.gd — 主场景入口
# 宝石闪电无限 (Gem Blitz Endless)
# ============================================================

onready var board = $Board
onready var board_bg = $BoardBackground

var _shake_intensity := 0.0
var _board_origin := Vector2.ZERO


func _ready():
	randomize()
	_board_origin = board.position
	board.add_to_group("board")

	# 连接信号
	GameManager.connect("combo_changed", self, "_on_combo")
	GameManager.connect("gems_matched", self, "_on_match")
	GameManager.connect("game_started", self, "_on_game_started")

	# 初始状态：等待主菜单
	GameManager.current_state = GameManager.GameState.MAIN_MENU


func _on_game_started():
	# 短暂延迟让棋盘入场动画完成，然后启动计时
	yield(get_tree().create_timer(0.8), "timeout")
	GameManager.begin_timer()


func _process(delta):
	if _shake_intensity > 0.5:
		board.position = _board_origin + Vector2(
			rand_range(-_shake_intensity, _shake_intensity),
			rand_range(-_shake_intensity, _shake_intensity))
		_shake_intensity = lerp(_shake_intensity, 0.0, 5.0 * delta)
	else:
		_shake_intensity = 0.0
		board.position = _board_origin


func _shake(intensity: float):
	_shake_intensity = max(_shake_intensity, intensity)


func _on_combo(combo):
	if combo >= 2:
		_shake(GameManager.get_screen_shake_intensity())


func _on_match(data):
	if data.get("count", 0) >= 4:
		_shake(4.0)


func _unhandled_input(event):
	if event is InputEventKey and event.pressed:
		if event.scancode == KEY_ESCAPE:
			if GameManager.current_state == GameManager.GameState.PAUSED:
				GameManager.resume_game()
			elif GameManager.current_state == GameManager.GameState.READY:
				GameManager.pause_game()
			elif GameManager.current_state == GameManager.GameState.MAIN_MENU:
				get_tree().quit()
		elif event.scancode == KEY_R:
			if GameManager.current_state == GameManager.GameState.GAME_OVER:
				GameManager.start_game()
