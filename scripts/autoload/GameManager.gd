extends Node
# ============================================================
# GameManager.gd — 全局游戏状态管理单例
# 宝石闪电无限 (Gem Blitz Endless) — 无尽街机模式
# ============================================================

signal score_changed(new_score)
signal combo_changed(combo_count)
signal combo_ended()
signal time_changed(remaining)
signal time_bonus(seconds)
signal game_state_changed(new_state)
signal game_over()
signal game_started()
signal gems_matched(match_data)
signal special_gem_created(gem, special_type)
signal powerup_collected(powerup_type)
signal multiplier_changed(multiplier)

enum GameState { LOADING, READY, SWAPPING, MATCHING, ELIMINATING, FALLING, PAUSED, GAME_OVER, MAIN_MENU }

# 基础宝石颜色（用于匹配）
enum GemColor { RED, ORANGE, BLUE, GREEN, PURPLE, YELLOW }

# 特殊宝石类型（叠加在颜色上）
enum SpecialType { NONE, STRIPED_H, STRIPED_V, WRAPPED, COLOR_BOMB }

# 道具类型
enum PowerupType { HAMMER, SHUFFLE }

const NORMAL_GEM_COUNT := 6
const BOARD_COLS := 8
const BOARD_ROWS := 8
const CELL_SIZE := 72
const BOARD_OFFSET := Vector2(52, 340)

# 宝石基础贴图路径（按 GemColor 顺序）
const GEM_TEXTURES := [
	"res://assets/sprites/gem_red.png",
	"res://assets/sprites/gem_orange.png",
	"res://assets/sprites/gem_blue.png",
	"res://assets/sprites/gem_green.png",
	"res://assets/sprites/gem_purple.png",
	"res://assets/sprites/gem_yellow.png",
]

# 宝石颜色值（用于粒子等特效）
const GEM_COLORS := [
	Color("#FF2233"),  # RED
	Color("#FF7100"),  # ORANGE
	Color("#0088FF"),  # BLUE
	Color("#00B844"),  # GREEN
	Color("#9922EE"),  # PURPLE
	Color("#FFCC00"),  # YELLOW
]

# 宝石浅色（高光用）
const GEM_COLORS_LIGHT := [
	Color("#FF8888"),  # RED
	Color("#FFD0AA"),  # ORANGE
	Color("#AAD0FF"),  # BLUE
	Color("#AAFFCC"),  # GREEN
	Color("#D0AAFF"),  # PURPLE
	Color("#FFEEBB"),  # YELLOW
]

# UI 颜色
const COLOR_BG_DEEP := Color("#0B0B16")
const COLOR_BG_MID := Color("#1C2F3A")
const COLOR_PANEL_DARK := Color("#142034")
const COLOR_PANEL_MID := Color("#1E3C5A")
const COLOR_BORDER := Color("#C0A8FF", 0.3)
const COLOR_GOLD := Color("#FFC726")
const COLOR_PURPLE_GLOW := Color("#CC44FF")
const COLOR_CYAN := Color("#88CCFF")

# ── 计时系统 ────────────────────────────────────────────
const INITIAL_TIME := 60.0
const LOW_TIME_THRESHOLD := 10.0
# 消除时间奖励
const TIME_BONUS_MATCH3 := 2.0
const TIME_BONUS_MATCH4 := 3.0
const TIME_BONUS_MATCH5 := 5.0
const TIME_BONUS_CHAIN := 1.0       # 每次连锁额外+1秒
const TIME_BONUS_SPECIAL := 3.0     # 特殊宝石激活基础加秒
const TIME_BONUS_BIG_CLEAR := 10.0  # 一次性消除15+宝石
const TIME_PENALTY_SHUFFLE := 3.0   # 无移动自动洗牌扣秒
# 道具时间奖励
const TIME_BONUS_HAMMER := 1.0
const TIME_BONUS_SHUFFLE_ITEM := 2.0

# ── 积分系统 ────────────────────────────────────────────
const BASE_POINTS_PER_GEM := 10
const SCORE_MATCH3 := 30
const SCORE_MATCH4 := 60
const SCORE_MATCH5 := 100
const SCORE_SPECIAL_ACTIVATE := 200
const SCORE_COLOR_BOMB := 800
const SCORE_HAMMER := 50
# 连锁倍率：chain 1=1x, 2=1.5x, 3=2x, 4=2.5x, 5+=3x
const CHAIN_MULTIPLIERS := [1.0, 1.0, 1.5, 2.0, 2.5, 3.0]

# ── 道具系统 ────────────────────────────────────────────
const MAX_POWERUP_STACK := 3
const POWERUP_DROP_CHANCE := 0.2  # 20% 掉落率
const POWERUP_SCORE_MILESTONE := 1000  # 每1000分里程碑

# ── 游戏状态 ────────────────────────────────────────────
var current_state: int = GameState.MAIN_MENU setget set_state
var score: int = 0 setget set_score
var combo_count: int = 0 setget set_combo
var max_combo: int = 0
var time_remaining: float = INITIAL_TIME setget set_time
var is_timer_running := false
var best_score: int = 0
var current_multiplier: float = 1.0

# 道具库存
var powerup_inventory = {
	PowerupType.HAMMER: 0,
	PowerupType.SHUFFLE: 0,
}
var _last_score_milestone := 0  # 上次触发道具掉落的分数里程碑
var _gems_eliminated_in_chain := 0  # 当前连锁中消除的宝石总数

# 高分榜（本地 Top 10）
var high_scores = []  # [{score: int, date: String}, ...]
const MAX_HIGH_SCORES := 10
const SAVE_PATH := "user://gem_blitz_save.json"


func _ready():
	pause_mode = PAUSE_MODE_PROCESS
	_load_save_data()


func _process(delta):
	if is_timer_running and current_state != GameState.PAUSED:
		time_remaining -= delta
		emit_signal("time_changed", time_remaining)
		if time_remaining <= 0:
			time_remaining = 0
			_end_game()


# ── 状态管理 ────────────────────────────────────────────
func set_state(v):
	if current_state == v:
		return
	current_state = v
	emit_signal("game_state_changed", v)


func is_input_allowed() -> bool:
	return current_state == GameState.READY


# ── 游戏流程 ────────────────────────────────────────────
func start_game():
	score = 0
	emit_signal("score_changed", 0)
	combo_count = 0
	max_combo = 0
	time_remaining = INITIAL_TIME
	is_timer_running = false
	current_multiplier = 1.0
	_last_score_milestone = 0
	_gems_eliminated_in_chain = 0
	powerup_inventory[PowerupType.HAMMER] = 0
	powerup_inventory[PowerupType.SHUFFLE] = 0
	self.current_state = GameState.LOADING
	emit_signal("game_started")


func begin_timer():
	is_timer_running = true
	self.current_state = GameState.READY


func _end_game():
	is_timer_running = false
	self.current_state = GameState.GAME_OVER
	_check_high_score()
	emit_signal("game_over")


func pause_game():
	if current_state != GameState.GAME_OVER and current_state != GameState.MAIN_MENU:
		is_timer_running = false
		self.current_state = GameState.PAUSED


func resume_game():
	if current_state == GameState.PAUSED:
		is_timer_running = true
		self.current_state = GameState.READY


# ── 计分 ────────────────────────────────────────────────
func set_score(v):
	score = v
	emit_signal("score_changed", score)
	_check_powerup_milestone()


func add_score(base_points: int):
	var m = get_chain_multiplier()
	var gained = int(base_points * m)
	self.score += gained
	return gained


func get_match_score(match_count: int) -> int:
	if match_count >= 5:
		return SCORE_MATCH5
	elif match_count >= 4:
		return SCORE_MATCH4
	else:
		return SCORE_MATCH3


# ── 连锁系统 ────────────────────────────────────────────
func set_combo(v):
	combo_count = v
	if combo_count > max_combo:
		max_combo = combo_count
	current_multiplier = get_chain_multiplier()
	emit_signal("multiplier_changed", current_multiplier)
	emit_signal("combo_changed", combo_count)


func increment_combo():
	self.combo_count += 1


func reset_combo():
	if combo_count > 0:
		emit_signal("combo_ended")
	_gems_eliminated_in_chain = 0
	self.combo_count = 0


func get_chain_multiplier() -> float:
	var idx = int(clamp(combo_count, 0, CHAIN_MULTIPLIERS.size() - 1))
	return CHAIN_MULTIPLIERS[idx]


func get_particle_intensity() -> float:
	return lerp(1.0, 3.0, clamp(float(combo_count) / 5.0, 0.0, 1.0))


func get_screen_shake_intensity() -> float:
	return lerp(2.0, 10.0, clamp(float(combo_count) / 5.0, 0.0, 1.0))


# ── 计时 ────────────────────────────────────────────────
func set_time(v):
	time_remaining = max(0.0, v)
	emit_signal("time_changed", time_remaining)


func add_time_bonus(seconds: float):
	time_remaining += seconds
	emit_signal("time_bonus", seconds)
	emit_signal("time_changed", time_remaining)


func get_match_time_bonus(match_count: int) -> float:
	if match_count >= 5:
		return TIME_BONUS_MATCH5
	elif match_count >= 4:
		return TIME_BONUS_MATCH4
	else:
		return TIME_BONUS_MATCH3


func is_low_time() -> bool:
	return time_remaining <= LOW_TIME_THRESHOLD and time_remaining > 0


# ── 消除追踪 ────────────────────────────────────────────
func track_eliminated(count: int):
	_gems_eliminated_in_chain += count
	if _gems_eliminated_in_chain >= 15:
		add_time_bonus(TIME_BONUS_BIG_CLEAR)
		_gems_eliminated_in_chain = 0  # 重置，避免重复触发


# ── 道具系统 ────────────────────────────────────────────
func add_powerup(type: int):
	if powerup_inventory[type] < MAX_POWERUP_STACK:
		powerup_inventory[type] += 1
		emit_signal("powerup_collected", type)


func use_powerup(type: int) -> bool:
	if powerup_inventory[type] > 0:
		powerup_inventory[type] -= 1
		return true
	return false


func get_powerup_count(type: int) -> int:
	return powerup_inventory.get(type, 0)


func _check_powerup_milestone():
	var milestone = int(score / POWERUP_SCORE_MILESTONE) * POWERUP_SCORE_MILESTONE
	if milestone > _last_score_milestone and milestone > 0:
		_last_score_milestone = milestone
		if randf() < POWERUP_DROP_CHANCE:
			var type = PowerupType.HAMMER if randf() < 0.5 else PowerupType.SHUFFLE
			add_powerup(type)


func should_drop_powerup(chain_count: int) -> bool:
	if chain_count >= 10:
		return randf() < POWERUP_DROP_CHANCE
	return false


# ── 高分系统 ────────────────────────────────────────────
func _check_high_score():
	var entry = {"score": score, "date": _get_date_string()}
	high_scores.append(entry)
	high_scores.sort_custom(self, "_sort_scores")
	if high_scores.size() > MAX_HIGH_SCORES:
		high_scores.resize(MAX_HIGH_SCORES)
	if high_scores.size() > 0:
		best_score = high_scores[0].get("score", 0)
	_save_data()


func _sort_scores(a, b) -> bool:
	return a.get("score", 0) > b.get("score", 0)


func is_new_record() -> bool:
	return score >= best_score and score > 0


func _get_date_string() -> String:
	var dt = OS.get_datetime()
	return "%04d-%02d-%02d" % [dt.year, dt.month, dt.day]


# ── 存档 ────────────────────────────────────────────────
func _save_data():
	var file = File.new()
	if file.open(SAVE_PATH, File.WRITE) != OK:
		return
	var data = {
		"high_scores": high_scores,
		"best_score": best_score,
	}
	file.store_string(JSON.print(data))
	file.close()


func _load_save_data():
	var file = File.new()
	if not file.file_exists(SAVE_PATH):
		return
	if file.open(SAVE_PATH, File.READ) != OK:
		return
	var text = file.get_as_text()
	file.close()
	var result = JSON.parse(text)
	if result.error != OK:
		return
	var data = result.result
	high_scores = data.get("high_scores", [])
	best_score = int(data.get("best_score", 0))


# ── 坐标转换 ────────────────────────────────────────────
func grid_to_pixel(col: int, row: int) -> Vector2:
	return BOARD_OFFSET + Vector2(col * CELL_SIZE + CELL_SIZE * 0.5, row * CELL_SIZE + CELL_SIZE * 0.5)


func pixel_to_grid(pixel_pos: Vector2) -> Vector2:
	var local = pixel_pos - BOARD_OFFSET
	return Vector2(int(local.x / CELL_SIZE), int(local.y / CELL_SIZE))


func is_valid_cell(col: int, row: int) -> bool:
	return col >= 0 and col < BOARD_COLS and row >= 0 and row < BOARD_ROWS
