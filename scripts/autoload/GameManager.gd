extends Node
# ============================================================
# GameManager.gd — 全局游戏状态管理单例
# ============================================================

signal score_changed(new_score)
signal combo_changed(combo_count)
signal combo_ended()
signal moves_changed(remaining)
signal game_state_changed(new_state)
signal level_completed()
signal level_failed()
signal gems_matched(match_data)

enum GameState { LOADING, READY, SWAPPING, MATCHING, ELIMINATING, FALLING, PAUSED, GAME_OVER }
enum GemType { RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, STRIPED_H, STRIPED_V, BOMB, RAINBOW }

const NORMAL_GEM_COUNT := 6
const BOARD_COLS := 8
const BOARD_ROWS := 8
const CELL_SIZE := 72
const BOARD_OFFSET := Vector2(52, 340)

# 宝石贴图路径（按 GemType 顺序）
const GEM_TEXTURES := [
	"res://assets/sprites/gem_red.png",
	"res://assets/sprites/gem_orange.png",
	"res://assets/sprites/gem_yellow.png",
	"res://assets/sprites/gem_green.png",
	"res://assets/sprites/gem_blue.png",
	"res://assets/sprites/gem_purple.png",
	"res://assets/sprites/gem_striped_h.png",
	"res://assets/sprites/gem_striped_v.png",
	"res://assets/sprites/gem_bomb.png",
	"res://assets/sprites/gem_rainbow.png",
]

var current_state: int = GameState.LOADING setget set_state
var score: int = 0 setget set_score
var combo_count: int = 0 setget set_combo
var max_combo: int = 0
var moves_remaining: int = 30 setget set_moves
var current_level: int = 1

const COMBO_MULTIPLIERS := [1.0, 1.0, 1.5, 2.0, 3.0, 5.0]

func _ready():
	pause_mode = PAUSE_MODE_PROCESS

func set_state(v):
	if current_state == v:
		return
	current_state = v
	emit_signal("game_state_changed", v)

func is_input_allowed() -> bool:
	return current_state == GameState.READY

func set_score(v):
	score = v
	emit_signal("score_changed", score)

func add_score(base_points: int):
	var m = get_combo_multiplier()
	self.score += int(base_points * m)

func set_combo(v):
	combo_count = v
	if combo_count > max_combo:
		max_combo = combo_count
	emit_signal("combo_changed", combo_count)

func increment_combo():
	self.combo_count += 1

func reset_combo():
	if combo_count > 0:
		emit_signal("combo_ended")
	self.combo_count = 0

func get_combo_multiplier() -> float:
	var idx = int(clamp(combo_count, 0, COMBO_MULTIPLIERS.size() - 1))
	return COMBO_MULTIPLIERS[idx]

func get_particle_intensity() -> float:
	return lerp(1.0, 3.0, clamp(float(combo_count) / 5.0, 0.0, 1.0))

func get_screen_shake_intensity() -> float:
	return lerp(2.0, 10.0, clamp(float(combo_count) / 5.0, 0.0, 1.0))

func set_moves(v):
	moves_remaining = v
	emit_signal("moves_changed", moves_remaining)
	if moves_remaining <= 0:
		_check_game_over()

func use_move():
	self.moves_remaining -= 1

func start_level(level_id: int):
	current_level = level_id
	self.score = 0
	self.combo_count = 0
	max_combo = 0
	self.current_state = GameState.LOADING

func _check_game_over():
	if moves_remaining <= 0:
		self.current_state = GameState.GAME_OVER
		emit_signal("level_failed")

func complete_level():
	self.current_state = GameState.GAME_OVER
	emit_signal("level_completed")

func grid_to_pixel(col: int, row: int) -> Vector2:
	return BOARD_OFFSET + Vector2(col * CELL_SIZE + CELL_SIZE * 0.5, row * CELL_SIZE + CELL_SIZE * 0.5)

func pixel_to_grid(pixel_pos: Vector2) -> Vector2:
	var local = pixel_pos - BOARD_OFFSET
	return Vector2(int(local.x / CELL_SIZE), int(local.y / CELL_SIZE))

func is_valid_cell(col: int, row: int) -> bool:
	return col >= 0 and col < BOARD_COLS and row >= 0 and row < BOARD_ROWS
