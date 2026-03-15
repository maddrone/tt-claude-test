extends Node
# ============================================================
# LevelManager.gd — 简化为无尽模式辅助
# 保留接口兼容性，不再管理关卡流程
# ============================================================

signal level_loaded(level_data)

func _ready() -> void:
	pause_mode = PAUSE_MODE_PROCESS
	print("[LevelManager] 无尽模式，无关卡管理")


func get_gem_type_count() -> int:
	return GameManager.NORMAL_GEM_COUNT
