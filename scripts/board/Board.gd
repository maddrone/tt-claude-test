extends Node2D
# ============================================================
# Board.gd — 棋盘核心逻辑
# 宝石闪电无限 (Gem Blitz Endless)
# 特殊宝石生成、激活、组合效果、自动洗牌
# ============================================================

onready var gems_container: Node2D = $GemsContainer
onready var effects_container: Node2D = $EffectsContainer

var gem_scene: PackedScene = preload("res://scenes/gem/Gem.tscn")

var grid = []  # grid[col][row] = Gem or null
var selected_gem = null
var is_processing := false
var is_using_powerup := false  # 道具使用模式
var active_powerup: int = -1

var touch_start_pos := Vector2.ZERO
var is_touching := false
const SWIPE_THRESHOLD := 15.0


func _ready():
	_init_grid()
	_fill_board_no_matches()
	_play_entrance_animation()
	GameManager.connect("game_started", self, "_on_game_started")


func _on_game_started():
	_clear_board()
	_init_grid()
	_fill_board_no_matches()
	_play_entrance_animation()


func _play_entrance_animation():
	for col in range(GameManager.BOARD_COLS):
		for row in range(GameManager.BOARD_ROWS):
			var gem = grid[col][row]
			if gem:
				var drop_from = GameManager.BOARD_OFFSET.y - 200
				gem.spawn_drop(drop_from, (col + row) * 0.02)


func _clear_board():
	for col in range(GameManager.BOARD_COLS):
		for row in range(GameManager.BOARD_ROWS):
			if grid.size() > col and grid[col].size() > row and grid[col][row] != null:
				grid[col][row].queue_free()
	grid.clear()


func _init_grid():
	grid.clear()
	for col in range(GameManager.BOARD_COLS):
		var column = []
		for _row in range(GameManager.BOARD_ROWS):
			column.append(null)
		grid.append(column)


func _fill_board_no_matches():
	for col in range(GameManager.BOARD_COLS):
		for row in range(GameManager.BOARD_ROWS):
			var type = randi() % GameManager.NORMAL_GEM_COUNT
			while col >= 2 and _grid_color(col-1, row) == type and _grid_color(col-2, row) == type:
				type = randi() % GameManager.NORMAL_GEM_COUNT
			while row >= 2 and _grid_color(col, row-1) == type and _grid_color(col, row-2) == type:
				type = randi() % GameManager.NORMAL_GEM_COUNT
			_create_gem(type, col, row)


func _grid_color(col: int, row: int) -> int:
	if not GameManager.is_valid_cell(col, row):
		return -1
	if grid[col][row] == null:
		return -1
	return grid[col][row].gem_color


func _create_gem(color: int, col: int, row: int, special: int = GameManager.SpecialType.NONE):
	var gem = gem_scene.instance()
	gems_container.add_child(gem)
	gem.init(color, col, row, special)
	grid[col][row] = gem
	return gem


# ── 输入 ──────────────────────────────────────────────────
func _input(event):
	if not GameManager.is_input_allowed() or is_processing:
		return

	# 道具使用模式 - 锤子
	if is_using_powerup and active_powerup == GameManager.PowerupType.HAMMER:
		if event is InputEventMouseButton and event.pressed:
			_handle_hammer_use(event.position)
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

	# 检查特殊宝石组合
	var combo_result = _check_special_combo(gem_a, gem_b)
	if combo_result:
		_do_swap(gem_a, gem_b)
		yield(get_tree().create_timer(0.18), "timeout")
		yield(_execute_special_combo(gem_a, gem_b, combo_result), "completed")
		# 处理后续连锁
		var matches = _find_all_matches()
		if matches.size() > 0:
			yield(_process_match_chain(matches), "completed")
		_post_chain_check()
		is_processing = false
		GameManager.current_state = GameManager.GameState.READY
		return

	# 颜色炸弹 + 任意宝石
	if gem_a.is_color_bomb() or gem_b.is_color_bomb():
		_do_swap(gem_a, gem_b)
		yield(get_tree().create_timer(0.18), "timeout")
		var bomb = gem_a if gem_a.is_color_bomb() else gem_b
		var target = gem_b if gem_a.is_color_bomb() else gem_a
		yield(_activate_color_bomb(bomb, target.gem_color), "completed")
		var matches = _find_all_matches()
		if matches.size() > 0:
			yield(_process_match_chain(matches), "completed")
		_post_chain_check()
		is_processing = false
		GameManager.current_state = GameManager.GameState.READY
		return

	_do_swap(gem_a, gem_b)
	yield(get_tree().create_timer(0.18), "timeout")

	var matches = _find_all_matches()
	if matches.size() > 0:
		yield(_process_match_chain(matches), "completed")
		_post_chain_check()
	else:
		_do_swap(gem_a, gem_b)
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
# 返回匹配信息数组，每个元素包含 {gems: [], direction: "h"/"v", length: int}
func _find_all_match_groups() -> Array:
	var groups = []

	# 水平
	for row in range(GameManager.BOARD_ROWS):
		var col = 0
		while col < GameManager.BOARD_COLS:
			var color = _grid_color(col, row)
			if color < 0:
				col += 1
				continue
			var end = col + 1
			while end < GameManager.BOARD_COLS and _grid_color(end, row) == color:
				end += 1
			if end - col >= 3:
				var gems = []
				for c in range(col, end):
					if grid[c][row] != null:
						gems.append(grid[c][row])
				groups.append({"gems": gems, "direction": "h", "length": end - col})
			col = end

	# 垂直
	for col in range(GameManager.BOARD_COLS):
		var row = 0
		while row < GameManager.BOARD_ROWS:
			var color = _grid_color(col, row)
			if color < 0:
				row += 1
				continue
			var end = row + 1
			while end < GameManager.BOARD_ROWS and _grid_color(col, end) == color:
				end += 1
			if end - row >= 3:
				var gems = []
				for r in range(row, end):
					if grid[col][r] != null:
						gems.append(grid[col][r])
				groups.append({"gems": gems, "direction": "v", "length": end - row})
			row = end

	return groups


func _find_all_matches() -> Array:
	var matched = {}
	var groups = _find_all_match_groups()
	for group in groups:
		for gem in group.gems:
			matched["%d_%d" % [gem.grid_col, gem.grid_row]] = true

	var result = []
	for key in matched:
		var parts = key.split("_")
		var c = int(parts[0])
		var r = int(parts[1])
		if grid[c][r] != null:
			result.append(grid[c][r])
	return result


# ── 特殊宝石生成检测 ──────────────────────────────────────
# 在消除前检测匹配形状，决定是否生成特殊宝石
func _detect_special_gem_spawns(match_groups: Array) -> Array:
	var spawns = []  # [{col, row, color, special_type}, ...]

	# 先检测 L/T 形（包裹宝石）- 找交叉点
	var cell_groups = {}  # "col_row" -> [group indices]
	for i in range(match_groups.size()):
		for gem in match_groups[i].gems:
			var key = "%d_%d" % [gem.grid_col, gem.grid_row]
			if not cell_groups.has(key):
				cell_groups[key] = []
			cell_groups[key].append(i)

	var used_groups = {}

	# L/T 形：一个宝石同时属于水平和垂直匹配组
	for key in cell_groups:
		if cell_groups[key].size() >= 2:
			var has_h = false
			var has_v = false
			for gi in cell_groups[key]:
				if match_groups[gi].direction == "h":
					has_h = true
				if match_groups[gi].direction == "v":
					has_v = true
			if has_h and has_v:
				var parts = key.split("_")
				var col = int(parts[0])
				var row = int(parts[1])
				var color = _grid_color(col, row)
				spawns.append({
					"col": col, "row": row,
					"color": color,
					"special_type": GameManager.SpecialType.WRAPPED
				})
				for gi in cell_groups[key]:
					used_groups[gi] = true

	# 5连：颜色炸弹
	for i in range(match_groups.size()):
		if used_groups.has(i):
			continue
		if match_groups[i].length >= 5:
			var gems = match_groups[i].gems
			var mid = gems[int(gems.size() / 2)]
			spawns.append({
				"col": mid.grid_col, "row": mid.grid_row,
				"color": -1,  # 颜色炸弹无颜色
				"special_type": GameManager.SpecialType.COLOR_BOMB
			})
			used_groups[i] = true

	# 4连：条纹宝石
	for i in range(match_groups.size()):
		if used_groups.has(i):
			continue
		if match_groups[i].length == 4:
			var gems = match_groups[i].gems
			var mid = gems[1]  # 第二个位置
			var st = GameManager.SpecialType.STRIPED_V if match_groups[i].direction == "h" else GameManager.SpecialType.STRIPED_H
			spawns.append({
				"col": mid.grid_col, "row": mid.grid_row,
				"color": mid.gem_color,
				"special_type": st
			})
			used_groups[i] = true

	return spawns


# ── 特殊宝石组合检测 ──────────────────────────────────────
func _check_special_combo(gem_a, gem_b) -> String:
	var sa = gem_a.special_type
	var sb = gem_b.special_type
	if sa == GameManager.SpecialType.NONE and sb == GameManager.SpecialType.NONE:
		return ""

	# 彩色炸弹 + 彩色炸弹 = 全屏清除
	if gem_a.is_color_bomb() and gem_b.is_color_bomb():
		return "bomb_bomb"

	# 彩色炸弹 + 条纹 = 全屏同色变条纹
	if gem_a.is_color_bomb() and (sb == GameManager.SpecialType.STRIPED_H or sb == GameManager.SpecialType.STRIPED_V):
		return "bomb_striped"
	if gem_b.is_color_bomb() and (sa == GameManager.SpecialType.STRIPED_H or sa == GameManager.SpecialType.STRIPED_V):
		return "bomb_striped"

	# 彩色炸弹 + 包裹 = 全屏同色变包裹
	if gem_a.is_color_bomb() and sb == GameManager.SpecialType.WRAPPED:
		return "bomb_wrapped"
	if gem_b.is_color_bomb() and sa == GameManager.SpecialType.WRAPPED:
		return "bomb_wrapped"

	# 条纹 + 条纹 = 十字清除
	if (sa == GameManager.SpecialType.STRIPED_H or sa == GameManager.SpecialType.STRIPED_V) and \
	   (sb == GameManager.SpecialType.STRIPED_H or sb == GameManager.SpecialType.STRIPED_V):
		return "striped_striped"

	# 包裹 + 包裹 = 5x5 大爆炸
	if sa == GameManager.SpecialType.WRAPPED and sb == GameManager.SpecialType.WRAPPED:
		return "wrapped_wrapped"

	# 条纹 + 包裹 = 大范围行列清除
	if (sa == GameManager.SpecialType.STRIPED_H or sa == GameManager.SpecialType.STRIPED_V) and sb == GameManager.SpecialType.WRAPPED:
		return "striped_wrapped"
	if sa == GameManager.SpecialType.WRAPPED and (sb == GameManager.SpecialType.STRIPED_H or sb == GameManager.SpecialType.STRIPED_V):
		return "striped_wrapped"

	return ""


# ── 特殊组合执行 ──────────────────────────────────────────
func _execute_special_combo(gem_a, gem_b, combo_type: String):
	AudioManager.play_sfx("special_explode")
	GameManager.add_score(GameManager.SCORE_COLOR_BOMB)
	GameManager.add_time_bonus(GameManager.TIME_BONUS_SPECIAL * 2)

	var center_col = gem_b.grid_col
	var center_row = gem_b.grid_row
	var to_eliminate = []

	match combo_type:
		"bomb_bomb":
			# 清除全屏
			for col in range(GameManager.BOARD_COLS):
				for row in range(GameManager.BOARD_ROWS):
					if grid[col][row] != null:
						to_eliminate.append(grid[col][row])

		"bomb_striped":
			# 全屏同色变条纹后激活
			var bomb = gem_a if gem_a.is_color_bomb() else gem_b
			var striped = gem_b if gem_a.is_color_bomb() else gem_a
			var target_color = striped.gem_color
			# 消除彩色炸弹
			if bomb and is_instance_valid(bomb):
				to_eliminate.append(bomb)
			# 找所有同色宝石，变成条纹后消除其行/列
			var affected_cells = []
			for col in range(GameManager.BOARD_COLS):
				for row in range(GameManager.BOARD_ROWS):
					if grid[col][row] != null and grid[col][row].gem_color == target_color:
						affected_cells.append(Vector2(col, row))
						to_eliminate.append(grid[col][row])
			# 清除受影响行/列
			for cell in affected_cells:
				for c in range(GameManager.BOARD_COLS):
					if grid[c][int(cell.y)] != null and not grid[c][int(cell.y)] in to_eliminate:
						to_eliminate.append(grid[c][int(cell.y)])
				for r in range(GameManager.BOARD_ROWS):
					if grid[int(cell.x)][r] != null and not grid[int(cell.x)][r] in to_eliminate:
						to_eliminate.append(grid[int(cell.x)][r])

		"bomb_wrapped":
			# 全屏同色变包裹后大爆炸
			var bomb = gem_a if gem_a.is_color_bomb() else gem_b
			var wrapped = gem_b if gem_a.is_color_bomb() else gem_a
			var target_color = wrapped.gem_color
			if bomb and is_instance_valid(bomb):
				to_eliminate.append(bomb)
			for col in range(GameManager.BOARD_COLS):
				for row in range(GameManager.BOARD_ROWS):
					if grid[col][row] != null and grid[col][row].gem_color == target_color:
						to_eliminate.append(grid[col][row])
						# 3x3 爆炸
						for dc in range(-1, 2):
							for dr in range(-1, 2):
								var nc = col + dc
								var nr = row + dr
								if GameManager.is_valid_cell(nc, nr) and grid[nc][nr] != null:
									if not grid[nc][nr] in to_eliminate:
										to_eliminate.append(grid[nc][nr])

		"striped_striped":
			# 交叉消除：2行 + 2列（以交换位置为中心）
			for c in range(GameManager.BOARD_COLS):
				if grid[c][gem_a.grid_row] != null and not grid[c][gem_a.grid_row] in to_eliminate:
					to_eliminate.append(grid[c][gem_a.grid_row])
				if grid[c][gem_b.grid_row] != null and not grid[c][gem_b.grid_row] in to_eliminate:
					to_eliminate.append(grid[c][gem_b.grid_row])
			for r in range(GameManager.BOARD_ROWS):
				if grid[gem_a.grid_col][r] != null and not grid[gem_a.grid_col][r] in to_eliminate:
					to_eliminate.append(grid[gem_a.grid_col][r])
				if grid[gem_b.grid_col][r] != null and not grid[gem_b.grid_col][r] in to_eliminate:
					to_eliminate.append(grid[gem_b.grid_col][r])

		"wrapped_wrapped":
			# 5x5 超大范围爆炸
			for dc in range(-2, 3):
				for dr in range(-2, 3):
					var nc = center_col + dc
					var nr = center_row + dr
					if GameManager.is_valid_cell(nc, nr) and grid[nc][nr] != null:
						if not grid[nc][nr] in to_eliminate:
							to_eliminate.append(grid[nc][nr])

		"striped_wrapped":
			# 5x1行 + 5x1列大范围清除（以中心为基准各5行5列）
			var sc = gem_b.grid_col
			var sr = gem_b.grid_row
			for dc in range(-2, 3):
				for c in range(GameManager.BOARD_COLS):
					var nr = sr + dc
					if GameManager.is_valid_cell(c, nr) and grid[c][nr] != null:
						if not grid[c][nr] in to_eliminate:
							to_eliminate.append(grid[c][nr])
			for dr in range(-2, 3):
				for r in range(GameManager.BOARD_ROWS):
					var nc = sc + dr
					if GameManager.is_valid_cell(nc, r) and grid[nc][r] != null:
						if not grid[nc][r] in to_eliminate:
							to_eliminate.append(grid[nc][r])

	# 执行消除
	if to_eliminate.size() > 0:
		GameManager.increment_combo()
		GameManager.track_eliminated(to_eliminate.size())
		_spawn_effects_for_gems(to_eliminate)
		var delay = 0.0
		for gem in to_eliminate:
			if gem and is_instance_valid(gem):
				grid[gem.grid_col][gem.grid_row] = null
				gem.eliminate(delay)
				delay += 0.01
		yield(get_tree().create_timer(delay + 0.3), "timeout")
		GameManager.current_state = GameManager.GameState.FALLING
		yield(_collapse_and_refill(), "completed")
	else:
		yield(get_tree(), "idle_frame")


# ── 特殊宝石激活 ──────────────────────────────────────────
func _activate_special_gem(gem) -> Array:
	var to_eliminate = []
	if not gem or not is_instance_valid(gem):
		return to_eliminate

	AudioManager.play_sfx("special_explode")
	GameManager.add_score(GameManager.SCORE_SPECIAL_ACTIVATE)
	GameManager.add_time_bonus(GameManager.TIME_BONUS_SPECIAL)

	match gem.special_type:
		GameManager.SpecialType.STRIPED_H:
			# 消除整行
			var row = gem.grid_row
			for c in range(GameManager.BOARD_COLS):
				if grid[c][row] != null and not grid[c][row] in to_eliminate:
					to_eliminate.append(grid[c][row])

		GameManager.SpecialType.STRIPED_V:
			# 消除整列
			var col = gem.grid_col
			for r in range(GameManager.BOARD_ROWS):
				if grid[col][r] != null and not grid[col][r] in to_eliminate:
					to_eliminate.append(grid[col][r])

		GameManager.SpecialType.WRAPPED:
			# 3x3 范围爆炸
			for dc in range(-1, 2):
				for dr in range(-1, 2):
					var nc = gem.grid_col + dc
					var nr = gem.grid_row + dr
					if GameManager.is_valid_cell(nc, nr) and grid[nc][nr] != null:
						if not grid[nc][nr] in to_eliminate:
							to_eliminate.append(grid[nc][nr])

	return to_eliminate


func _activate_color_bomb(bomb, target_color: int):
	AudioManager.play_sfx("special_explode")
	GameManager.add_score(GameManager.SCORE_COLOR_BOMB)
	GameManager.add_time_bonus(GameManager.TIME_BONUS_SPECIAL * 2)
	GameManager.increment_combo()

	var to_eliminate = [bomb]
	for col in range(GameManager.BOARD_COLS):
		for row in range(GameManager.BOARD_ROWS):
			if grid[col][row] != null and grid[col][row].gem_color == target_color:
				if not grid[col][row] in to_eliminate:
					to_eliminate.append(grid[col][row])

	GameManager.track_eliminated(to_eliminate.size())
	_spawn_effects_for_gems(to_eliminate)
	var delay = 0.0
	for gem in to_eliminate:
		if gem and is_instance_valid(gem):
			grid[gem.grid_col][gem.grid_row] = null
			gem.eliminate(delay)
			delay += 0.02
	yield(get_tree().create_timer(delay + 0.3), "timeout")
	GameManager.current_state = GameManager.GameState.FALLING
	yield(_collapse_and_refill(), "completed")


# ── 消除链 ────────────────────────────────────────────────
func _process_match_chain(matched_gems: Array):
	GameManager.reset_combo()

	while matched_gems.size() > 0:
		GameManager.increment_combo()
		GameManager.current_state = GameManager.GameState.ELIMINATING

		# 检测特殊宝石生成
		var match_groups = _find_all_match_groups()
		var special_spawns = _detect_special_gem_spawns(match_groups)

		# 计分
		for group in match_groups:
			var pts = GameManager.get_match_score(group.length)
			GameManager.add_score(pts)

		# 时间奖励
		for group in match_groups:
			var bonus = GameManager.get_match_time_bonus(group.length)
			GameManager.add_time_bonus(bonus)
		if GameManager.combo_count >= 2:
			GameManager.add_time_bonus(GameManager.TIME_BONUS_CHAIN)

		# 音效
		var max_len = 0
		for group in match_groups:
			max_len = max(max_len, group.length)
		if max_len >= 5:
			AudioManager.play_sfx("match5")
		elif max_len >= 4:
			AudioManager.play_sfx("match4")
		else:
			AudioManager.play_sfx("match3")

		if GameManager.combo_count >= 2:
			AudioManager.play_combo_sfx(GameManager.combo_count)

		# 收集需要保留的特殊宝石生成位置
		var spawn_positions = {}
		for spawn in special_spawns:
			spawn_positions["%d_%d" % [spawn.col, spawn.row]] = spawn

		# 发送匹配事件
		GameManager.track_eliminated(matched_gems.size())

		# 检测被消除的特殊宝石 - 它们需要先激活
		var special_eliminations = []
		for gem in matched_gems:
			if gem and is_instance_valid(gem) and gem.is_special():
				var key = "%d_%d" % [gem.grid_col, gem.grid_row]
				if not spawn_positions.has(key):
					special_eliminations.append(gem)

		# 激活被消除的特殊宝石
		var extra_elims = []
		for special_gem in special_eliminations:
			var activated = _activate_special_gem(special_gem)
			for g in activated:
				if not g in matched_gems and not g in extra_elims:
					extra_elims.append(g)

		# 合并额外消除
		for g in extra_elims:
			if not g in matched_gems:
				matched_gems.append(g)

		# 特效
		_spawn_effects_for_gems(matched_gems)

		# 消除动画（跳过特殊生成位置的宝石）
		var delay = 0.0
		for gem in matched_gems:
			if gem and is_instance_valid(gem):
				var key = "%d_%d" % [gem.grid_col, gem.grid_row]
				grid[gem.grid_col][gem.grid_row] = null
				if not spawn_positions.has(key):
					gem.eliminate(delay)
					delay += 0.02
				else:
					gem.queue_free()

		# 生成特殊宝石
		for key in spawn_positions:
			var spawn = spawn_positions[key]
			var new_gem = _create_gem(spawn.color, spawn.col, spawn.row, spawn.special_type)
			new_gem.play_special_create_anim()
			AudioManager.play_sfx("special_create")
			GameManager.emit_signal("special_gem_created", new_gem, spawn.special_type)

		yield(get_tree().create_timer(delay + 0.3), "timeout")

		# 道具掉落检查
		if GameManager.should_drop_powerup(matched_gems.size()):
			var type = GameManager.PowerupType.HAMMER if randf() < 0.5 else GameManager.PowerupType.SHUFFLE
			GameManager.add_powerup(type)

		# 下落填充
		GameManager.current_state = GameManager.GameState.FALLING
		yield(_collapse_and_refill(), "completed")

		# 检查新匹配
		matched_gems = _find_all_matches()

	GameManager.reset_combo()


# ── 特效生成 ──────────────────────────────────────────────
func _spawn_effects_for_gems(gems: Array):
	for gem in gems:
		if gem and is_instance_valid(gem):
			# 分数飘字
			var popup = load("res://scripts/effects/ScorePopup.gd").new()
			effects_container.add_child(popup)
			var color = Color.white
			if gem.gem_color >= 0 and gem.gem_color < GameManager.GEM_COLORS.size():
				color = GameManager.GEM_COLORS[gem.gem_color]
			var pts = int(GameManager.BASE_POINTS_PER_GEM * GameManager.get_chain_multiplier())
			popup.show_score(pts, gem.position, color)

			# 粒子效果
			var effect = load("res://scripts/effects/MatchEffect.gd").new()
			effects_container.add_child(effect)
			effect.create_burst(gem.position, color, GameManager.combo_count)


# ── 下落填充 ──────────────────────────────────────────────
func _collapse_and_refill():
	var max_delay = 0.0

	for col in range(GameManager.BOARD_COLS):
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

		var new_count = 0
		for row in range(write_row, -1, -1):
			var type = randi() % GameManager.NORMAL_GEM_COUNT
			var gem = _create_gem(type, col, row)
			var from_y = GameManager.BOARD_OFFSET.y - (new_count + 1) * GameManager.CELL_SIZE
			var d = (write_row - row + 1) * 0.04
			gem.spawn_drop(from_y, d)
			max_delay = max(max_delay, d)
			new_count += 1

	yield(get_tree().create_timer(max_delay + 0.3), "timeout")


# ── 无移动检测与自动洗牌 ──────────────────────────────────
func _post_chain_check():
	if not _has_valid_moves():
		_auto_shuffle()


func _has_valid_moves() -> bool:
	for col in range(GameManager.BOARD_COLS):
		for row in range(GameManager.BOARD_ROWS):
			if grid[col][row] == null:
				continue
			# 颜色炸弹总是可交换
			if grid[col][row].is_color_bomb():
				return true
			# 检查右方交换
			if col + 1 < GameManager.BOARD_COLS and grid[col+1][row] != null:
				_do_swap_silent(col, row, col+1, row)
				if _find_all_matches().size() > 0:
					_do_swap_silent(col+1, row, col, row)
					return true
				_do_swap_silent(col+1, row, col, row)
			# 检查下方交换
			if row + 1 < GameManager.BOARD_ROWS and grid[col][row+1] != null:
				_do_swap_silent(col, row, col, row+1)
				if _find_all_matches().size() > 0:
					_do_swap_silent(col, row+1, col, row)
					return true
				_do_swap_silent(col, row+1, col, row)
	return false


func _do_swap_silent(c1: int, r1: int, c2: int, r2: int):
	var temp = grid[c1][r1]
	grid[c1][r1] = grid[c2][r2]
	grid[c2][r2] = temp


func _auto_shuffle():
	GameManager.add_time_bonus(-GameManager.TIME_PENALTY_SHUFFLE)
	# 收集所有宝石颜色
	var colors = []
	for col in range(GameManager.BOARD_COLS):
		for row in range(GameManager.BOARD_ROWS):
			if grid[col][row] != null:
				colors.append(grid[col][row].gem_color)
	# 洗牌
	for i in range(colors.size() - 1, 0, -1):
		var j = randi() % (i + 1)
		var temp = colors[i]
		colors[i] = colors[j]
		colors[j] = temp
	# 重新分配（保留特殊类型）
	var idx = 0
	for col in range(GameManager.BOARD_COLS):
		for row in range(GameManager.BOARD_ROWS):
			if grid[col][row] != null and idx < colors.size():
				grid[col][row].gem_color = colors[idx]
				grid[col][row]._apply_texture()
				idx += 1
	# 确保有有效移动
	if not _has_valid_moves():
		_auto_shuffle()


# ── 道具：锤子 ──────────────────────────────────────────
func enter_hammer_mode():
	if GameManager.use_powerup(GameManager.PowerupType.HAMMER):
		is_using_powerup = true
		active_powerup = GameManager.PowerupType.HAMMER
		_deselect()


func cancel_powerup_mode():
	is_using_powerup = false
	active_powerup = -1


func _handle_hammer_use(pos: Vector2):
	var gp = GameManager.pixel_to_grid(pos)
	var col = int(gp.x)
	var row = int(gp.y)
	if not GameManager.is_valid_cell(col, row) or grid[col][row] == null:
		cancel_powerup_mode()
		return

	is_using_powerup = false
	active_powerup = -1
	is_processing = true

	var gem = grid[col][row]
	GameManager.add_score(GameManager.SCORE_HAMMER)
	GameManager.add_time_bonus(GameManager.TIME_BONUS_HAMMER)
	AudioManager.play_sfx("special_explode")

	# 如果是特殊宝石，激活它
	if gem.is_special():
		var extra = _activate_special_gem(gem)
		var to_elim = [gem]
		for g in extra:
			if not g in to_elim:
				to_elim.append(g)
		_spawn_effects_for_gems(to_elim)
		for g in to_elim:
			if g and is_instance_valid(g):
				grid[g.grid_col][g.grid_row] = null
				g.eliminate(0)
	else:
		grid[col][row] = null
		_spawn_effects_for_gems([gem])
		gem.eliminate(0)

	yield(get_tree().create_timer(0.35), "timeout")

	GameManager.current_state = GameManager.GameState.FALLING
	yield(_collapse_and_refill(), "completed")

	var matches = _find_all_matches()
	if matches.size() > 0:
		yield(_process_match_chain(matches), "completed")

	_post_chain_check()
	is_processing = false
	GameManager.current_state = GameManager.GameState.READY


# ── 道具：刷新 ──────────────────────────────────────────
func use_shuffle():
	if not GameManager.use_powerup(GameManager.PowerupType.SHUFFLE):
		return
	is_processing = true
	GameManager.add_time_bonus(GameManager.TIME_BONUS_SHUFFLE_ITEM)
	_auto_shuffle()
	is_processing = false
