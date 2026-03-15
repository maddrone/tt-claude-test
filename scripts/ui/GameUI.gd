extends CanvasLayer
# ============================================================
# GameUI.gd — 游戏 HUD
# 宝石闪电无限 (Gem Blitz Endless)
# 顶部：分数+最高分 | 时间条 | 暂停
# 中央：连击提示
# 右侧：道具栏
# 游戏结束/主菜单覆盖层
# ============================================================

# ── 节点引用 ──────────────────────────────────────────────
onready var score_label = $HUD/TopBar/ScorePanel/ScoreValue
onready var best_label = $HUD/TopBar/ScorePanel/BestValue
onready var multiplier_label = $HUD/TopBar/ScorePanel/MultiplierLabel
onready var timer_bar = $HUD/TopBar/TimerBarContainer/TimerBar
onready var timer_label = $HUD/TopBar/TimerBarContainer/TimerLabel
onready var pause_btn = $HUD/TopBar/PauseBtn
onready var combo_label = $HUD/ComboLabel
onready var time_bonus_label = $HUD/TimeBonusLabel
onready var hammer_btn = $HUD/PowerupBar/HammerBtn
onready var hammer_count = $HUD/PowerupBar/HammerBtn/CountLabel
onready var shuffle_btn = $HUD/PowerupBar/ShuffleBtn
onready var shuffle_count = $HUD/PowerupBar/ShuffleBtn/CountLabel
onready var main_menu_panel = $MainMenuPanel
onready var game_over_panel = $GameOverPanel

var _combo_tween: Tween
var _timer_tween: Tween
var _time_bonus_tween: Tween
var _low_time_flashing := false


func _ready():
	_combo_tween = Tween.new()
	add_child(_combo_tween)
	_timer_tween = Tween.new()
	add_child(_timer_tween)
	_time_bonus_tween = Tween.new()
	add_child(_time_bonus_tween)

	# 连接信号
	GameManager.connect("score_changed", self, "_on_score")
	GameManager.connect("time_changed", self, "_on_time")
	GameManager.connect("time_bonus", self, "_on_time_bonus")
	GameManager.connect("combo_changed", self, "_on_combo")
	GameManager.connect("combo_ended", self, "_on_combo_end")
	GameManager.connect("multiplier_changed", self, "_on_multiplier")
	GameManager.connect("game_over", self, "_on_game_over")
	GameManager.connect("game_started", self, "_on_game_started")
	GameManager.connect("powerup_collected", self, "_on_powerup_collected")

	# 按钮
	pause_btn.connect("pressed", self, "_on_pause_pressed")
	hammer_btn.connect("pressed", self, "_on_hammer_pressed")
	shuffle_btn.connect("pressed", self, "_on_shuffle_pressed")

	# 初始状态
	combo_label.visible = false
	time_bonus_label.visible = false
	game_over_panel.visible = false
	_update_powerup_display()
	_on_score(0)
	best_label.text = str(GameManager.best_score)

	# 显示主菜单
	_show_main_menu()


# ── 主菜单 ──────────────────────────────────────────────
func _show_main_menu():
	main_menu_panel.visible = true
	game_over_panel.visible = false


func _on_start_pressed():
	main_menu_panel.visible = false
	GameManager.start_game()


func _on_game_started():
	game_over_panel.visible = false
	main_menu_panel.visible = false
	_low_time_flashing = false
	_update_powerup_display()
	best_label.text = str(GameManager.best_score)
	multiplier_label.text = "x1"
	timer_bar.value = 100


# ── 分数 ────────────────────────────────────────────────
func _on_score(v):
	score_label.text = str(v)


func _on_multiplier(m):
	if m > 1.0:
		multiplier_label.text = "x%.1f" % m
		multiplier_label.add_color_override("font_color", GameManager.COLOR_GOLD)
	else:
		multiplier_label.text = "x1"
		multiplier_label.add_color_override("font_color", Color.white)


# ── 计时条 ──────────────────────────────────────────────
func _on_time(remaining):
	var pct = (remaining / GameManager.INITIAL_TIME) * 100.0
	timer_bar.value = clamp(pct, 0, 100)
	timer_label.text = "%ds" % int(ceil(remaining))

	# 颜色变化
	if remaining <= GameManager.LOW_TIME_THRESHOLD:
		timer_bar.modulate = Color("#FF4444")
		if not _low_time_flashing:
			_low_time_flashing = true
	elif remaining <= GameManager.INITIAL_TIME * 0.5:
		timer_bar.modulate = Color("#FFB800")
		_low_time_flashing = false
	else:
		timer_bar.modulate = Color("#44DD44")
		_low_time_flashing = false


func _on_time_bonus(seconds):
	time_bonus_label.visible = true
	if seconds > 0:
		time_bonus_label.text = "+%ds" % int(seconds)
		time_bonus_label.add_color_override("font_color", Color("#44FF44"))
	else:
		time_bonus_label.text = "-%ds" % int(abs(seconds))
		time_bonus_label.add_color_override("font_color", Color("#FF4444"))

	_time_bonus_tween.stop_all()
	time_bonus_label.rect_scale = Vector2(1.5, 1.5)
	time_bonus_label.modulate.a = 1.0
	_time_bonus_tween.interpolate_property(time_bonus_label, "rect_scale",
		Vector2(1.5, 1.5), Vector2.ONE, 0.2, Tween.TRANS_BACK, Tween.EASE_OUT)
	_time_bonus_tween.interpolate_property(time_bonus_label, "modulate:a",
		1.0, 0.0, 0.5, Tween.TRANS_QUAD, Tween.EASE_IN, 0.8)
	_time_bonus_tween.start()


# ── 连击 ────────────────────────────────────────────────
func _on_combo(combo):
	if combo < 2:
		return
	combo_label.visible = true
	combo_label.modulate.a = 1.0
	if combo >= 6:
		combo_label.text = "INCREDIBLE x%d!" % combo
		combo_label.add_color_override("font_color", Color("ff4444"))
	elif combo >= 4:
		combo_label.text = "AMAZING x%d!" % combo
		combo_label.add_color_override("font_color", Color("ff8844"))
	elif combo >= 3:
		combo_label.text = "GREAT x%d!" % combo
		combo_label.add_color_override("font_color", Color("ffcc00"))
	else:
		combo_label.text = "COMBO x%d!" % combo
		combo_label.add_color_override("font_color", Color.white)

	_combo_tween.stop_all()
	_combo_tween.interpolate_property(combo_label, "rect_scale",
		Vector2(1.5, 1.5), Vector2.ONE, 0.2, Tween.TRANS_BACK, Tween.EASE_OUT)
	_combo_tween.start()


func _on_combo_end():
	_combo_tween.stop_all()
	_combo_tween.interpolate_property(combo_label, "modulate:a",
		1.0, 0.0, 0.3, Tween.TRANS_QUAD, Tween.EASE_IN)
	_combo_tween.start()
	yield(_combo_tween, "tween_all_completed")
	combo_label.visible = false
	combo_label.modulate.a = 1.0


# ── 道具 ────────────────────────────────────────────────
func _update_powerup_display():
	var h = GameManager.get_powerup_count(GameManager.PowerupType.HAMMER)
	var s = GameManager.get_powerup_count(GameManager.PowerupType.SHUFFLE)
	hammer_count.text = str(h)
	shuffle_count.text = str(s)
	hammer_btn.disabled = h <= 0
	shuffle_btn.disabled = s <= 0


func _on_powerup_collected(_type):
	_update_powerup_display()


func _on_hammer_pressed():
	if GameManager.current_state != GameManager.GameState.READY:
		return
	var board = get_tree().get_nodes_in_group("board")
	if board.size() > 0:
		board[0].enter_hammer_mode()
	_update_powerup_display()


func _on_shuffle_pressed():
	if GameManager.current_state != GameManager.GameState.READY:
		return
	var board = get_tree().get_nodes_in_group("board")
	if board.size() > 0:
		board[0].use_shuffle()
	_update_powerup_display()


# ── 暂停 ────────────────────────────────────────────────
func _on_pause_pressed():
	if GameManager.current_state == GameManager.GameState.PAUSED:
		GameManager.resume_game()
		pause_btn.text = "||"
	elif GameManager.current_state == GameManager.GameState.READY:
		GameManager.pause_game()
		pause_btn.text = ">"


# ── 游戏结束 ────────────────────────────────────────────
func _on_game_over():
	game_over_panel.visible = true
	var final_score_label = game_over_panel.get_node("VBox/FinalScoreLabel")
	final_score_label.text = str(GameManager.score)
	var record_label = game_over_panel.get_node("VBox/RecordLabel")
	if GameManager.is_new_record():
		record_label.text = "NEW RECORD!"
		record_label.add_color_override("font_color", GameManager.COLOR_GOLD)
		record_label.visible = true
	else:
		record_label.visible = false

	var best = game_over_panel.get_node("VBox/BestScoreLabel")
	best.text = "BEST: %d" % GameManager.best_score


func _on_replay_pressed():
	game_over_panel.visible = false
	GameManager.start_game()


func _on_menu_pressed():
	game_over_panel.visible = false
	_show_main_menu()


func _on_highscore_pressed():
	var list_label = main_menu_panel.get_node("VBox/HighScoreList")
	list_label.visible = not list_label.visible
	if list_label.visible:
		var text = ""
		if GameManager.high_scores.size() == 0:
			text = "No scores yet!"
		else:
			for i in range(min(GameManager.high_scores.size(), 10)):
				var entry = GameManager.high_scores[i]
				text += "%d. %d  (%s)\n" % [i + 1, int(entry.get("score", 0)), entry.get("date", "")]
		list_label.text = text
