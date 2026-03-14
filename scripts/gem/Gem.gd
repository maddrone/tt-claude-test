extends Node2D
# ============================================================
# Gem.gd — 宝石节点（使用 Sprite 贴图）
# ============================================================

signal gem_selected(gem)
signal move_completed(gem)

var gem_type: int = -1
var grid_col: int = 0
var grid_row: int = 0
var is_selected: bool = false
var is_matched: bool = false
var is_moving: bool = false
var is_special: bool = false

const MOVE_DURATION := 0.15
const FALL_DURATION := 0.2
const ELIMINATE_DURATION := 0.25
const SELECT_SCALE := 1.12
const BOUNCE_SCALE := 1.2
const GEM_DISPLAY_SIZE := 60.0  # 宝石显示像素尺寸

onready var sprite: Sprite = $Sprite
onready var select_ring: Sprite = $SelectRing
onready var tween: Tween = $Tween

# 预加载的贴图缓存
var _texture_cache = {}

func get_gem_texture(type: int) -> Texture:
	if _texture_cache.has(type):
		return _texture_cache[type]
	if type >= 0 and type < GameManager.GEM_TEXTURES.size():
		var tex = load(GameManager.GEM_TEXTURES[type])
		_texture_cache[type] = tex
		return tex
	return null


func _ready():
	select_ring.visible = false
	if gem_type >= 0:
		_apply_texture()


func init(type: int, col: int, row: int):
	gem_type = type
	grid_col = col
	grid_row = row
	is_special = type >= GameManager.NORMAL_GEM_COUNT
	position = GameManager.grid_to_pixel(col, row)
	_apply_texture()


func _apply_texture():
	if sprite == null:
		return
	var tex = get_gem_texture(gem_type)
	if tex:
		sprite.texture = tex
		# 缩放贴图到目标显示尺寸
		var tex_size = tex.get_size()
		if tex_size.x > 0:
			var s = GEM_DISPLAY_SIZE / tex_size.x
			sprite.scale = Vector2(s, s)


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
	"""从指定 y 坐标掉落到当前位置（出场动画）"""
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


func _on_input_event(_viewport, event, _shape_idx):
	if not GameManager.is_input_allowed():
		return
	if event is InputEventMouseButton and event.pressed:
		emit_signal("gem_selected", self)
