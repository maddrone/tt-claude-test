extends Node2D
# ============================================================
# Gem.gd — 宝石节点
# 支持基础颜色 + 特殊类型（程序化绘制标记）
# ============================================================

var gem_color: int = -1       # GemColor 枚举（0-5），COLOR_BOMB 时为 -1
var special_type: int = GameManager.SpecialType.NONE
var grid_col: int = 0
var grid_row: int = 0
var is_selected: bool = false
var is_matched: bool = false
var is_moving: bool = false

const MOVE_DURATION := 0.15
const FALL_DURATION := 0.2
const ELIMINATE_DURATION := 0.25
const SELECT_SCALE := 1.12
const BOUNCE_SCALE := 1.2
const GEM_DISPLAY_SIZE := 60.0

onready var sprite: Sprite = $Sprite
onready var select_ring: Sprite = $SelectRing
onready var tween: Tween = $Tween

var _texture_cache = {}


func get_gem_texture(color_idx: int) -> Texture:
	if _texture_cache.has(color_idx):
		return _texture_cache[color_idx]
	if color_idx >= 0 and color_idx < GameManager.GEM_TEXTURES.size():
		var tex = load(GameManager.GEM_TEXTURES[color_idx])
		_texture_cache[color_idx] = tex
		return tex
	return null


func _ready():
	select_ring.visible = false
	if gem_color >= 0:
		_apply_texture()


func init(color: int, col: int, row: int, special: int = GameManager.SpecialType.NONE):
	gem_color = color
	special_type = special
	grid_col = col
	grid_row = row
	position = GameManager.grid_to_pixel(col, row)
	_apply_texture()
	update()  # 触发 _draw() 绘制特殊标记


func set_special(special: int):
	special_type = special
	_apply_texture()
	update()


func is_special() -> bool:
	return special_type != GameManager.SpecialType.NONE


func is_color_bomb() -> bool:
	return special_type == GameManager.SpecialType.COLOR_BOMB


func get_match_color() -> int:
	return gem_color


func _apply_texture():
	if sprite == null:
		return
	if special_type == GameManager.SpecialType.COLOR_BOMB:
		# 彩色炸弹使用彩虹纹理
		var tex = load("res://assets/sprites/gem_rainbow.png")
		if tex:
			sprite.texture = tex
			var tex_size = tex.get_size()
			if tex_size.x > 0:
				sprite.scale = Vector2(GEM_DISPLAY_SIZE / tex_size.x, GEM_DISPLAY_SIZE / tex_size.x)
		return
	# 所有其他宝石（包括特殊）都使用基础颜色纹理
	var tex = get_gem_texture(gem_color)
	if tex:
		sprite.texture = tex
		var tex_size = tex.get_size()
		if tex_size.x > 0:
			var s = GEM_DISPLAY_SIZE / tex_size.x
			sprite.scale = Vector2(s, s)


# ── 程序化绘制特殊宝石标记 ──────────────────────────────
func _draw():
	match special_type:
		GameManager.SpecialType.STRIPED_H:
			_draw_striped_h()
		GameManager.SpecialType.STRIPED_V:
			_draw_striped_v()
		GameManager.SpecialType.WRAPPED:
			_draw_wrapped()


func _draw_striped_h():
	# 三条水平白色条纹
	var half = GEM_DISPLAY_SIZE * 0.4
	var stripe_color = Color(1, 1, 1, 0.7)
	var w = 2.5
	for i in [-1, 0, 1]:
		var y = i * 8.0
		draw_line(Vector2(-half, y), Vector2(half, y), stripe_color, w)
	# 两侧小三角箭头
	var arrow_color = Color(1, 1, 1, 0.9)
	draw_line(Vector2(-half - 2, 0), Vector2(-half + 6, -5), arrow_color, 2.0)
	draw_line(Vector2(-half - 2, 0), Vector2(-half + 6, 5), arrow_color, 2.0)
	draw_line(Vector2(half + 2, 0), Vector2(half - 6, -5), arrow_color, 2.0)
	draw_line(Vector2(half + 2, 0), Vector2(half - 6, 5), arrow_color, 2.0)


func _draw_striped_v():
	# 三条垂直白色条纹
	var half = GEM_DISPLAY_SIZE * 0.4
	var stripe_color = Color(1, 1, 1, 0.7)
	var w = 2.5
	for i in [-1, 0, 1]:
		var x = i * 8.0
		draw_line(Vector2(x, -half), Vector2(x, half), stripe_color, w)
	# 上下小三角箭头
	var arrow_color = Color(1, 1, 1, 0.9)
	draw_line(Vector2(0, -half - 2), Vector2(-5, -half + 6), arrow_color, 2.0)
	draw_line(Vector2(0, -half - 2), Vector2(5, -half + 6), arrow_color, 2.0)
	draw_line(Vector2(0, half + 2), Vector2(-5, half - 6), arrow_color, 2.0)
	draw_line(Vector2(0, half + 2), Vector2(5, half - 6), arrow_color, 2.0)


func _draw_wrapped():
	# 菱形包裹框
	var r = GEM_DISPLAY_SIZE * 0.38
	var wrap_color = Color(1, 1, 1, 0.8)
	var w = 2.5
	# 外框菱形
	draw_line(Vector2(0, -r), Vector2(r, 0), wrap_color, w)
	draw_line(Vector2(r, 0), Vector2(0, r), wrap_color, w)
	draw_line(Vector2(0, r), Vector2(-r, 0), wrap_color, w)
	draw_line(Vector2(-r, 0), Vector2(0, -r), wrap_color, w)
	# 四角小圆点
	var dot_color = Color(1, 1, 1, 0.9)
	var dot_r = 3.0
	draw_circle(Vector2(0, -r), dot_r, dot_color)
	draw_circle(Vector2(r, 0), dot_r, dot_color)
	draw_circle(Vector2(0, r), dot_r, dot_color)
	draw_circle(Vector2(-r, 0), dot_r, dot_color)


func set_selected(selected: bool):
	is_selected = selected
	select_ring.visible = selected
	tween.stop_all()
	if selected:
		tween.interpolate_property(self, "scale", scale, Vector2.ONE * SELECT_SCALE,
			0.12, Tween.TRANS_BACK, Tween.EASE_OUT)
	else:
		tween.interpolate_property(self, "scale", scale, Vector2.ONE,
			0.08, Tween.TRANS_QUAD, Tween.EASE_OUT)
	tween.start()


func move_to_cell(col: int, row: int, duration := MOVE_DURATION):
	grid_col = col
	grid_row = row
	is_moving = true
	var target = GameManager.grid_to_pixel(col, row)
	tween.stop_all()
	tween.interpolate_property(self, "position", position, target,
		duration, Tween.TRANS_QUAD, Tween.EASE_IN_OUT)
	tween.start()


func fall_to_cell(col: int, row: int, delay: float = 0.0):
	grid_col = col
	grid_row = row
	is_moving = true
	var target = GameManager.grid_to_pixel(col, row)
	if delay > 0.0:
		yield(get_tree().create_timer(delay), "timeout")
	tween.stop_all()
	tween.interpolate_property(self, "position", position, target,
		FALL_DURATION, Tween.TRANS_BOUNCE, Tween.EASE_OUT)
	tween.start()


func eliminate(delay: float = 0.0):
	is_matched = true
	if delay > 0.0:
		yield(get_tree().create_timer(delay), "timeout")
	if not is_inside_tree():
		return
	tween.stop_all()
	tween.interpolate_property(self, "scale",
		Vector2.ONE, Vector2.ONE * BOUNCE_SCALE,
		ELIMINATE_DURATION * 0.3, Tween.TRANS_QUAD, Tween.EASE_OUT)
	tween.interpolate_property(self, "scale",
		Vector2.ONE * BOUNCE_SCALE, Vector2.ZERO,
		ELIMINATE_DURATION * 0.7, Tween.TRANS_BACK, Tween.EASE_IN,
		ELIMINATE_DURATION * 0.3)
	tween.interpolate_property(self, "modulate:a", 1.0, 0.0,
		ELIMINATE_DURATION, Tween.TRANS_QUAD, Tween.EASE_IN)
	tween.start()
	yield(tween, "tween_all_completed")
	queue_free()


func spawn_drop(from_y: float, delay: float = 0.0):
	var target = position
	position.y = from_y
	modulate.a = 1.0
	scale = Vector2.ONE
	if delay > 0.0:
		yield(get_tree().create_timer(delay), "timeout")
	if not is_inside_tree():
		return
	tween.stop_all()
	tween.interpolate_property(self, "position", position, target,
		FALL_DURATION, Tween.TRANS_BOUNCE, Tween.EASE_OUT)
	tween.start()


func play_special_create_anim():
	if not is_inside_tree():
		return
	tween.stop_all()
	tween.interpolate_property(self, "scale",
		Vector2.ONE * 1.5, Vector2.ONE,
		0.3, Tween.TRANS_BACK, Tween.EASE_OUT)
	tween.interpolate_property(self, "modulate",
		Color(2, 2, 2, 1), Color(1, 1, 1, 1),
		0.3, Tween.TRANS_QUAD, Tween.EASE_OUT)
	tween.start()
