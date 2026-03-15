extends Node2D
# ============================================================
# Board.gd — 棋盘核心逻辑（完全重写，简化可靠版本）
# ============================================================

onready var gems_container: Node2D = $GemsContainer
onready var effects_container: Node2D = $EffectsContainer

var gem_scene: PackedScene = preload("res://scenes/gem/Gem.tscn")

var grid = []  # grid[col][row] = Gem or null
var selected_gem = null
var is_processing := false

var touch_start_pos := Vector2.ZERO
var is_touching := false
const SWIPE_THRESHOLD := 15.0


func _ready():
	_init_grid()
	_fill_board_no_matches()
	# 出场动画
	for col in range(GameManager.BOARD_COLS):
		for row in range(GameManager.BOARD_ROWS):
			var gem = grid[col][row]
			if gem:
				var drop_from = GameManager.BOARD_OFFSET.y - 200
				gem.spawn_drop(drop_from, (col + row) * 0.02)
	GameManager.current_state = GameManager.GameState.READY


func _init_grid():
	grid.clear()
	for col in range(GameManager.BOARD_COLS):
		var column = []
		for _row in range(GameManager.BOARD_ROWS):
			column.append(null)
		grid.append(column)


func _fill_board_no_matches():
	"""填充棋盘，确保没有初始三连"""
	var gem_count = LevelManager.get_gem_type_count()
	for col in range(GameManager.BOARD_COLS):
		for row in range(GameManager.BOARD_ROWS):
			var type = randi() % gem_count
			# 避免水平三连
			while col >= 2 and _grid_type(col-1, row) == type and _grid_type(col-2, row) == type:
				type = randi() % gem_count
			# 避免垂直三连
			while row >= 2 and _grid_type(col, row-1) == type and _grid_type(col, row-2) == type:
				type = randi() % gem_count
			_create_gem(type, col, row)


func _grid_type(col: int, row: int) -> int:
	"""安全获取网格位置的宝石类型"""
	if col < 0 or col >= GameManager.BOARD_COLS or row < 0 or row >= GameManager.BOARD_ROWS:
		return -1
	if grid[col][row] == null:
		return -1
	return grid[col][row].gem_type


func _create_gem(type: int, col: int, row: int):
	var gem = gem_scene.instance()
	gems_container.add_child(gem)
	gem.init(type, col, row)
	gem.connect("gem_selected", self, "_on_gem_selected")
	grid[col][row] = gem
	return gem


# ── 输入 ──────────────────────────────────────────────────
func _input(event):
	if not GameManager.is_input_allowed() or is_processing:
		return

	if event is InputEventMouseButton:
		var pos = event.position
		if event.pressed:
			touch_start_pos = pos
			is_touching = true
			_handle_touch(pos)
		else:
			if is_touching and selected_gem and pos.distance_to(touch_start_pos) > SWIPE_THRESHOLD:
				_handle_swipe(pos)
			is_touching = false

	if event is InputEventMouseMotion and is_touching and selected_gem:
		if event.position.distance_to(touch_start_pos) > SWIPE_THRESHOLD:
			_handle_swipe(event.position)
			is_touching = false


func _handle_touch(pos: Vector2):
	var gp = GameManager.pixel_to_grid(pos)
	var col = int(gp.x)
	var row = int(gp.y)
	if not GameManager.is_valid_cell(col, row):
		return
	if grid[col][row] == null:
		return

	var gem = grid[col][row]
	if selected_gem == null:
		_select_gem(gem)
	elif selected_gem == gem:
		_deselect()
	elif _are_adjacent(selected_gem, gem):
		_try_swap(selected_gem, gem)
	else:
		_deselect()
		_select_gem(gem)


func _handle_swipe(end_pos: Vector2):
	if selected_gem == null:
		return
	var delta = end_pos - touch_start_pos
	var dir = Vector2.ZERO
	if abs(delta.x) > abs(delta.y):
		dir = Vector2(sign(delta.x), 0)
	else:
		dir = Vector2(0, sign(delta.y))

	var tc = selected_gem.grid_col + int(dir.x)
	var tr = selected_gem.grid_row + int(dir.y)
	if GameManager.is_valid_cell(tc, tr) and grid[tc][tr] != null:
		_try_swap(selected_gem, grid[tc][tr])
	else:
		_deselect()


func _on_gem_selected(gem):
	if is_processing:
		return
	if selected_gem == null:
		_select_gem(gem)
	elif selected_gem == gem:
		_deselect()
	elif _are_adjacent(selected_gem, gem):
		_try_swap(selected_gem, gem)
	else:
		_deselect()
		_select_gem(gem)


func _select_gem(gem):
	selected_gem = gem
	gem.set_selected(true)
	AudioManager.play_sfx("button_click")


func _deselect():
	if selected_gem:
		selected_gem.set_selected(false)
		selected_gem = null


func _are_adjacent(a, b) -> bool:
	return (abs(a.grid_col - b.grid_col) + abs(a.grid_row - b.grid_row)) == 1


# ── 交换 ──────────────────────────────────────────────────
func _try_swap(gem_a, gem_b):
	_deselect()
	is_processing = true
	GameManager.current_state = GameManager.GameState.SWAPPING
	AudioManager.play_sfx("swap")

	_do_swap(gem_a, gem_b)
	yield(get_tree().create_timer(0.18), "timeout")

	var matches = _find_all_matches()
	if matches.size() > 0:
		GameManager.use_move()
		yield(_process_match_chain(matches), "completed")
	else:
		_do_swap(gem_a, gem_b)  # 换回去
		yield(get_tree().create_timer(0.18), "timeout")

	is_processing = false
	GameManager.current_state = GameManager.GameState.READY


func _do_swap(a, b):
	var ca = a.grid_col; var ra = a.grid_row
	var cb = b.grid_col; var rb = b.grid_row
	grid[ca][ra] = b
	grid[cb][rb] = a
	a.move_to_cell(cb, rb)
	b.move_to_cell(ca, ra)


# ── 匹配检测 ──────────────────────────────────────────────
func _find_all_matches() -> Array:
	"""扫描全部三连及以上匹配"""
	var matched = {}  # "col_row" -> true

	# 水平
	for row in range(GameManager.BOARD_ROWS):
		var col = 0
		while col < GameManager.BOARD_COLS:
			var type = _grid_type(col, row)
			if type < 0:
				col += 1
				continue
			var end = col + 1
			while end < GameManager.BOARD_COLS and _grid_type(end, row) == type:
				end += 1
			if end - col >= 3:
				for c in range(col, end):
					matched["%d_%d" % [c, row]] = true
			col = end

	# 垂直
	for col in range(GameManager.BOARD_COLS):
		var row = 0
		while row < GameManager.BOARD_ROWS:
			var type = _grid_type(col, row)
			if type < 0:
				row += 1
				continue
			var end = row + 1
			while end < GameManager.BOARD_ROWS and _grid_type(col, end) == type:
				end += 1
			if end - row >= 3:
				for r in range(row, end):
					matched["%d_%d" % [col, r]] = true
			row = end

	# 收集宝石
	var result = []
	for key in matched:
		var parts = key.split("_")
		var c = int(parts[0])
		var r = int(parts[1])
		if grid[c][r] != null:
			result.append(grid[c][r])
	return result


# ── 消除链 ────────────────────────────────────────────────
func _process_match_chain(matched_gems: Array):
	GameManager.reset_combo()

	while matched_gems.size() > 0:
		GameManager.increment_combo()
		GameManager.current_state = GameManager.GameState.ELIMINATING

		# 计分
		var base = 10 * matched_gems.size()
		GameManager.add_score(base)

		# 音效
		if matched_gems.size() >= 5:
			AudioManager.play_sfx("match5")
		elif matched_gems.size() >= 4:
			AudioManager.play_sfx("match4")
		else:
			AudioManager.play_sfx("match3")

		if GameManager.combo_count >= 2:
			AudioManager.play_combo_sfx(GameManager.combo_count)

		# 发送匹配事件
		for gem in matched_gems:
			GameManager.emit_signal("gems_matched", {
				"type": gem.gem_type, "count": 1
			})

		# 消除动画
		var delay = 0.0
		for gem in matched_gems:
			if gem and is_instance_valid(gem):
				grid[gem.grid_col][gem.grid_row] = null
				gem.eliminate(delay)
				delay += 0.02

		yield(get_tree().create_timer(delay + 0.3), "timeout")

		# 下落填充
		GameManager.current_state = GameManager.GameState.FALLING
		yield(_collapse_and_refill(), "completed")

		# 检查新匹配
		matched_gems = _find_all_matches()

	GameManager.reset_combo()


# ── 下落填充 ──────────────────────────────────────────────
func _collapse_and_refill():
	var gem_count = LevelManager.get_gem_type_count()
	var max_delay = 0.0

	for col in range(GameManager.BOARD_COLS):
		# 下落：从底部向上扫描
		var write_row = GameManager.BOARD_ROWS - 1
		for row in range(GameManager.BOARD_ROWS - 1, -1, -1):
			if grid[col][row] != null:
				if row != write_row:
					var gem = grid[col][row]
					grid[col][row] = null
					grid[col][write_row] = gem
					var d = (write_row - row) * 0.03
					gem.fall_to_cell(col, write_row, d)
					max_delay = max(max_delay, d)
				write_row -= 1

		# 填充新宝石
		var new_count = 0
		for row in range(write_row, -1, -1):
			var type = randi() % gem_count
			var gem = _create_gem(type, col, row)
			var from_y = GameManager.BOARD_OFFSET.y - (new_count + 1) * GameManager.CELL_SIZE
			var d = (write_row - row + 1) * 0.04
			gem.spawn_drop(from_y, d)
			max_delay = max(max_delay, d)
			new_count += 1

	yield(get_tree().create_timer(max_delay + 0.3), "timeout")
