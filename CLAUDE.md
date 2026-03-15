# Godot 3.5 LTS 低性能设备游戏开发规范

## 项目概况

这是一个基于 Godot 3.5 LTS 的「宝石闪电无限 (Gem Blitz Endless)」街机三消游戏项目。无尽模式，计时制，目标平台为低性能 Android 设备。使用 GLES2 渲染器。

核心玩法：60秒计时 + 特殊宝石（条纹/包裹/彩色炸弹）+ 道具系统（锤子/刷新）+ 连锁时间奖励 + 本地高分榜。

## Godot 3.x 开发必须遵守的规则

以下规则均来自实际调试中遇到的严重 Bug，必须严格遵守。

### 1. 语法兼容性 — 不要使用 Godot 4.x 语法

Godot 3.x 不支持以下语法，使用会导致解析错误或运行时崩溃：

```gdscript
# 错误 - Godot 3 不支持 static var
static var my_var = 0
# 正确
var my_var = 0

# 错误 - Godot 3 空字典/数组不能用 :=
var dict := {}
var arr := []
# 正确
var dict = {}
var arr = []
```

### 2. JSON 数据类型 — 所有数字都是 float

Godot 3 的 JSON 解析器将所有数字解析为 `float`。使用 `%` 运算符或需要 `int` 的地方必须手动转换：

```gdscript
# 错误 - JSON 中的数字是 float，% 运算符不接受 float
var count = json_data.get("count", 6)  # 返回 6.0 (float)
var result = randi() % count           # 崩溃！

# 正确
var count = int(json_data.get("count", 6))
var result = randi() % count           # OK
```

### 3. 输入系统 — 避免双重输入处理

`_input()` 和 Area2D 的 `_input_event` 会在同一帧处理同一个事件。在 Godot 3 中执行顺序是：
1. `_input()` — 先触发
2. Area2D `_input_event` — 后触发

如果两者都处理选中逻辑，会导致"选中后立即取消"的 Bug。

**规则：选择一种输入方式，不要混用。** 推荐使用 `_input()` + `pixel_to_grid()` 坐标转换，而非 Area2D 信号。

```gdscript
# 错误 - 同时使用两种输入
func _create_gem(type, col, row):
    gem.connect("gem_selected", self, "_on_gem_selected")  # Area2D 路径

func _input(event):
    _handle_touch(event.position)  # _input 路径
    # 两者冲突！同一帧内选中又取消

# 正确 - 只用一种
func _create_gem(type, col, row):
    # 不连接信号，统一由 _input 处理

func _input(event):
    _handle_touch(event.position)
```

### 4. 鼠标释放事件 — 防止零距离滑动

鼠标松开时，如果不检查滑动距离，`sign(0)` 返回 `0`，会导致宝石与自身交换：

```gdscript
# 错误
else:  # mouse released
    if is_touching and selected_gem:
        _handle_swipe(pos)  # delta=(0,0) 时尝试自交换

# 正确
else:
    if is_touching and selected_gem and pos.distance_to(touch_start_pos) > SWIPE_THRESHOLD:
        _handle_swipe(pos)
```

### 5. 节点初始化顺序 — _ready() 是从子到父

Godot 的 `_ready()` 调用顺序是**子节点先，父节点后**。如果子节点设置了某个全局状态，父节点的 `_ready()` 可能会覆盖它：

```gdscript
# Board._ready() 先执行 → 设置 state = READY
# Main._ready() 后执行 → 调用 load_level() → 设置 state = LOADING
# 结果：state 卡在 LOADING，输入被阻塞

# 修复：在父节点 _ready() 末尾确保状态正确
func _ready():
    LevelManager.load_level(1)
    GameManager.current_state = GameManager.GameState.READY  # 显式恢复
```

### 6. 资源尺寸一致性

生成的图片资源（如棋盘背景）的网格尺寸必须与代码中的 `CELL_SIZE` 一致。不一致会导致视觉错位：

```python
# generate_assets.py 中
BOARD_CELL = 72  # 必须与 GameManager.CELL_SIZE 一致
```

### 7. 信号声明 — 只声明会 emit 的信号

声明了但从未 `emit_signal()` 的信号会产生调试警告。如果信号不在当前脚本中 emit，不要在当前脚本中声明它。

### 8. 项目配置

- `config/icon` 引用的图标文件必须实际存在，否则会报 `load_image` 错误
- 使用 GLES2 渲染器以兼容低端设备
- stretch mode 设为 `2d`，aspect 设为 `keep_height`

## 低性能设备优化要点

- 使用 AudioStreamPlayer 对象池（而非运行时创建），SFX 池上限 8 个
- 避免运行时频繁创建/销毁节点，优先使用对象池
- 粒子效果强度根据设备能力调整
- GLES2 + 关闭 MSAA/FXAA
- framebuffer_allocation 设为最小

## 项目结构约定

```
scripts/
  autoload/          # 全局单例（GameManager, AudioManager, LevelManager）
  board/             # 棋盘逻辑
  gem/               # 宝石逻辑
  ui/                # UI 脚本
  effects/           # 特效脚本
scenes/              # 对应的 .tscn 场景文件
assets/
  sprites/           # PNG 图片资源
  audio/             # WAV 音效
  fonts/             # 字体文件
data/                # JSON 配置数据
tools/               # 资源生成脚本
```
