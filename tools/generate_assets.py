#!/usr/bin/env python3
"""
生成开心消消乐所需的全部图片资源
- 6种普通宝石（带渐变、高光、阴影的精美宝石）
- 特殊宝石（条纹、炸弹、彩虹）
- 棋盘背景
- 游戏背景
- 选中指示器
"""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSET_DIR = "/home/user/tt-claude-test/assets/sprites"

# ── 宝石配色（主色、亮色、暗色）──────────────────
GEM_CONFIGS = [
    {"name": "gem_red",    "main": (232, 72, 85),   "light": (255, 140, 148), "dark": (180, 40, 55),   "shape": "circle"},
    {"name": "gem_orange", "main": (247, 152, 36),   "light": (255, 200, 100), "dark": (200, 110, 10),  "shape": "diamond"},
    {"name": "gem_yellow", "main": (249, 220, 92),   "light": (255, 245, 170), "dark": (210, 175, 40),  "shape": "circle"},
    {"name": "gem_green",  "main": (59, 178, 115),   "light": (120, 220, 160), "dark": (30, 130, 75),   "shape": "diamond"},
    {"name": "gem_blue",   "main": (72, 149, 239),   "light": (140, 195, 255), "dark": (35, 100, 190),  "shape": "circle"},
    {"name": "gem_purple", "main": (155, 93, 229),   "light": (200, 160, 255), "dark": (110, 55, 180),  "shape": "diamond"},
]

SIZE = 128  # 宝石贴图尺寸
HALF = SIZE // 2
BOARD_CELL = 80


def create_radial_gradient(size, center, radius, color_center, color_edge):
    """创建径向渐变图像"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(size):
        for x in range(size):
            dx = x - center[0]
            dy = y - center[1]
            dist = math.sqrt(dx*dx + dy*dy)
            t = min(dist / radius, 1.0)
            # 平滑插值
            t = t * t * (3 - 2 * t)  # smoothstep
            r = int(color_center[0] * (1-t) + color_edge[0] * t)
            g = int(color_center[1] * (1-t) + color_edge[1] * t)
            b = int(color_center[2] * (1-t) + color_edge[2] * t)
            a = int(255 * (1 - t * 0.3))
            img.putpixel((x, y), (r, g, b, a))
    return img


def draw_gem_circle(draw, cx, cy, radius, main, light, dark):
    """绘制圆形宝石"""
    # 外圈阴影
    draw.ellipse([cx-radius-2, cy-radius+2, cx+radius-2, cy+radius+6],
                 fill=(0, 0, 0, 60))
    # 主体
    draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius],
                 fill=main)
    # 暗色边缘（下半部分）
    draw.ellipse([cx-radius+4, cy-4, cx+radius-4, cy+radius-4],
                 fill=dark)
    # 主色覆盖（上半部分）
    draw.ellipse([cx-radius+3, cy-radius+3, cx+radius-3, cy+radius//2+8],
                 fill=main)
    # 高光（左上角亮点）
    draw.ellipse([cx-radius//2-4, cy-radius//2-4, cx-radius//6+8, cy-radius//6+8],
                 fill=light + (200,))
    # 小高光点
    draw.ellipse([cx-radius//3, cy-radius//3, cx-radius//3+10, cy-radius//3+10],
                 fill=(255, 255, 255, 180))


def draw_gem_diamond(draw, cx, cy, radius, main, light, dark):
    """绘制菱形宝石"""
    r = radius
    # 阴影
    shadow = [(cx, cy-r+3), (cx+r+1, cy+3), (cx, cy+r+5), (cx-r+1, cy+3)]
    draw.polygon(shadow, fill=(0, 0, 0, 50))
    # 外框
    outer = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
    draw.polygon(outer, fill=dark)
    # 内部主色
    inner_r = r - 5
    inner = [(cx, cy-inner_r), (cx+inner_r, cy), (cx, cy+inner_r), (cx-inner_r, cy)]
    draw.polygon(inner, fill=main)
    # 上半高光
    top_r = r - 10
    top = [(cx, cy-top_r), (cx+top_r-5, cy-5), (cx, cy+2), (cx-top_r+5, cy-5)]
    draw.polygon(top, fill=light + (160,))
    # 亮点
    draw.ellipse([cx-8, cy-r//2-4, cx+4, cy-r//2+8],
                 fill=(255, 255, 255, 160))


def generate_gem(config):
    """生成一个宝石精灵图"""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = HALF, HALF
    radius = HALF - 12

    if config["shape"] == "circle":
        draw_gem_circle(draw, cx, cy, radius, config["main"], config["light"], config["dark"])
    else:
        draw_gem_diamond(draw, cx, cy, radius, config["main"], config["light"], config["dark"])

    # 轻微模糊让边缘更柔和
    img = img.filter(ImageFilter.SMOOTH_MORE)

    return img


def generate_special_striped_h():
    """横条纹特殊宝石"""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = HALF, HALF
    r = HALF - 12
    # 金色底
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255, 215, 0))
    draw.ellipse([cx-r+4, cy-r+4, cx+r-4, cy+r-4], fill=(255, 235, 80))
    # 横条纹
    for i in range(-3, 4):
        y = cy + i * 8
        draw.line([(cx-r+10, y), (cx+r-10, y)], fill=(255, 255, 255, 200), width=2)
    # 高光
    draw.ellipse([cx-15, cy-r//2-5, cx+5, cy-r//2+10], fill=(255, 255, 255, 150))
    return img.filter(ImageFilter.SMOOTH)


def generate_special_striped_v():
    """竖条纹特殊宝石"""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = HALF, HALF
    r = HALF - 12
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255, 215, 0))
    draw.ellipse([cx-r+4, cy-r+4, cx+r-4, cy+r-4], fill=(255, 235, 80))
    for i in range(-3, 4):
        x = cx + i * 8
        draw.line([(x, cy-r+10), (x, cy+r-10)], fill=(255, 255, 255, 200), width=2)
    draw.ellipse([cx-15, cy-r//2-5, cx+5, cy-r//2+10], fill=(255, 255, 255, 150))
    return img.filter(ImageFilter.SMOOTH)


def generate_special_bomb():
    """炸弹特殊宝石"""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = HALF, HALF
    r = HALF - 12
    # 深色球体
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(60, 60, 70))
    draw.ellipse([cx-r+3, cy-r+3, cx+r-3, cy-3], fill=(90, 90, 100))
    # X标记
    draw.line([(cx-15, cy-15), (cx+15, cy+15)], fill=(255, 80, 60), width=4)
    draw.line([(cx+15, cy-15), (cx-15, cy+15)], fill=(255, 80, 60), width=4)
    # 火花
    draw.ellipse([cx-4, cy-r-6, cx+8, cy-r+8], fill=(255, 160, 40))
    draw.ellipse([cx-2, cy-r-4, cx+6, cy-r+4], fill=(255, 220, 80))
    # 高光
    draw.ellipse([cx-12, cy-r//2-4, cx, cy-r//2+8], fill=(255, 255, 255, 100))
    return img.filter(ImageFilter.SMOOTH)


def generate_special_rainbow():
    """彩虹特殊宝石"""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = HALF, HALF
    r = HALF - 10

    # 彩虹色星形
    colors = [(255,0,0), (255,165,0), (255,255,0), (0,255,0), (0,150,255), (150,0,255)]
    points = 6
    for i in range(points):
        angle = (2 * math.pi * i / points) - math.pi / 2
        next_angle = (2 * math.pi * (i+1) / points) - math.pi / 2
        x1 = cx + int(r * math.cos(angle))
        y1 = cy + int(r * math.sin(angle))
        x2 = cx + int(r * math.cos(next_angle))
        y2 = cy + int(r * math.sin(next_angle))
        draw.polygon([(cx, cy), (x1, y1), (x2, y2)], fill=colors[i])

    # 白色中心
    draw.ellipse([cx-18, cy-18, cx+18, cy+18], fill=(255, 255, 255))
    draw.ellipse([cx-12, cy-12, cx+12, cy+12], fill=(255, 255, 240))
    # 星形高光
    draw.ellipse([cx-6, cy-6, cx+6, cy+6], fill=(255, 255, 255, 220))

    return img.filter(ImageFilter.SMOOTH)


def generate_select_ring():
    """选中指示器（发光环）"""
    img = Image.new("RGBA", (SIZE+32, SIZE+32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = (SIZE+32)//2, (SIZE+32)//2
    # 外发光
    for i in range(8, 0, -1):
        alpha = int(30 * (8-i) / 8)
        r = HALF + i + 4
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(255, 255, 100, alpha), width=2)
    # 主环
    r = HALF + 2
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(255, 255, 200, 200), width=3)
    return img


def generate_board_background():
    """棋盘背景（8x8 交替色格子 + 圆角外框）"""
    cols, rows = 8, 8
    padding = 8
    w = cols * BOARD_CELL + padding * 2
    h = rows * BOARD_CELL + padding * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 外框背景（深色半透明）
    draw.rounded_rectangle([0, 0, w-1, h-1], radius=16,
                           fill=(20, 18, 40, 200))

    # 格子
    for col in range(cols):
        for row in range(rows):
            x = padding + col * BOARD_CELL + 2
            y = padding + row * BOARD_CELL + 2
            cell_w = BOARD_CELL - 4
            if (col + row) % 2 == 0:
                color = (45, 42, 65, 220)
            else:
                color = (55, 52, 80, 220)
            draw.rounded_rectangle([x, y, x+cell_w, y+cell_w],
                                   radius=6, fill=color)

    return img


def generate_game_background():
    """游戏主背景（渐变星空风格）"""
    w, h = 720, 1280
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))

    # 垂直渐变（深蓝紫 → 深蓝）
    for y in range(h):
        t = y / h
        r = int(15 + 20 * t)
        g = int(10 + 15 * (1-t))
        b = int(40 + 30 * (1-t))
        for x in range(w):
            img.putpixel((x, y), (r, g, b, 255))

    draw = ImageDraw.Draw(img)
    # 随机星星
    import random
    random.seed(42)
    for _ in range(80):
        x = random.randint(0, w-1)
        y = random.randint(0, h-1)
        size = random.randint(1, 3)
        alpha = random.randint(80, 200)
        draw.ellipse([x, y, x+size, y+size], fill=(255, 255, 255, alpha))

    return img


def generate_particle():
    """粒子贴图（发光圆点）"""
    size = 32
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx, cy = size//2, size//2
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < size//2:
                t = dist / (size//2)
                alpha = int(255 * (1 - t*t))
                img.putpixel((x, y), (255, 255, 255, alpha))
    return img


def main():
    import os
    os.makedirs(ASSET_DIR, exist_ok=True)

    # 普通宝石
    for i, config in enumerate(GEM_CONFIGS):
        img = generate_gem(config)
        path = f"{ASSET_DIR}/{config['name']}.png"
        img.save(path)
        print(f"  [OK] {path}")

    # 特殊宝石
    specials = [
        ("gem_striped_h", generate_special_striped_h),
        ("gem_striped_v", generate_special_striped_v),
        ("gem_bomb", generate_special_bomb),
        ("gem_rainbow", generate_special_rainbow),
    ]
    for name, gen_func in specials:
        img = gen_func()
        path = f"{ASSET_DIR}/{name}.png"
        img.save(path)
        print(f"  [OK] {path}")

    # 选中指示器
    img = generate_select_ring()
    img.save(f"{ASSET_DIR}/select_ring.png")
    print(f"  [OK] select_ring.png")

    # 粒子
    img = generate_particle()
    img.save(f"{ASSET_DIR}/particle_glow.png")
    print(f"  [OK] particle_glow.png")

    # 棋盘背景
    img = generate_board_background()
    img.save(f"{ASSET_DIR}/board_bg.png")
    print(f"  [OK] board_bg.png")

    # 游戏背景
    img = generate_game_background()
    img.save(f"{ASSET_DIR}/game_bg.png")
    print(f"  [OK] game_bg.png")

    print("\n✅ 所有图片资源生成完成！")


if __name__ == "__main__":
    main()
