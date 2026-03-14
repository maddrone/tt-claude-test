extends CanvasLayer
# ============================================================
# GameUI.gd — 游戏 HUD
# ============================================================

onready var score_label = $MarginContainer/VBox/TopBar/ScoreLabel
onready var moves_label = $MarginContainer/VBox/TopBar/MovesLabel
onready var level_label = $MarginContainer/VBox/TopBar/LevelLabel
onready var combo_label = $ComboLabel

var _combo_tween: Tween


func _ready():
	_combo_tween = Tween.new()
	add_child(_combo_tween)

	combo_label.visible = false

	GameManager.connect("score_changed", self, "_on_score")
	GameManager.connect("moves_changed", self, "_on_moves")
	GameManager.connect("combo_changed", self, "_on_combo")
	GameManager.connect("combo_ended", self, "_on_combo_end")
	GameManager.connect("level_completed", self, "_on_win")
	GameManager.connect("level_failed", self, "_on_lose")
	LevelManager.connect("level_loaded", self, "_on_level")

	_on_score(0)
	_on_moves(30)


func _on_score(v):
	score_label.text = "SCORE\n%d" % v

func _on_moves(v):
	moves_label.text = "MOVES\n%d" % v
	if v <= 5:
		moves_label.add_color_override("font_color", Color("e84855"))
	else:
		moves_label.add_color_override("font_color", Color.white)

func _on_level(data):
	level_label.text = "LEVEL %d" % data.get("id", 1)
	_on_moves(data.get("moves", 30))

func _on_combo(combo):
	if combo < 2:
		return
	combo_label.visible = true
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

func _on_win():
	_show_popup("LEVEL CLEAR!", Color("3bb273"))

func _on_lose():
	_show_popup("GAME OVER", Color("e84855"))

func _show_popup(text: String, color: Color):
	var label = Label.new()
	label.text = text
	label.align = Label.ALIGN_CENTER
	label.valign = Label.VALIGN_CENTER
	label.rect_min_size = Vector2(400, 100)
	label.rect_position = Vector2(160, 550)
	label.add_color_override("font_color", color)
	add_child(label)
	label.rect_scale = Vector2.ZERO
	var t = Tween.new()
	add_child(t)
	t.interpolate_property(label, "rect_scale",
		Vector2.ZERO, Vector2(2.5, 2.5), 0.5, Tween.TRANS_BACK, Tween.EASE_OUT)
	t.start()
