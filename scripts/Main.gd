extends Node2D
# ============================================================
# Main.gd — 主场景入口
# ============================================================

onready var board = $Board
onready var board_bg = $BoardBackground
onready var shake_node = $Board  # 抖动棋盘节点而非 Camera

var _shake_intensity := 0.0
var _board_origin := Vector2.ZERO

func _ready():
	randomize()
	_board_origin = board.position
	LevelManager.load_level(1)
	# 连接抖动信号
	GameManager.connect("combo_changed", self, "_on_combo")
	GameManager.connect("gems_matched", self, "_on_match")


func _process(delta):
	# 屏幕抖动（直接抖棋盘节点）
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
			get_tree().quit()
		elif event.scancode == KEY_R:
			get_tree().reload_current_scene()
