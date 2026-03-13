"""
All rendering: gems, board, UI, animations, particles.
"""
import math
import random
import pygame
from board import (Board, Gem, EMPTY, SPECIAL_NONE, SPECIAL_HLINE,
                   SPECIAL_VLINE, SPECIAL_BOMB, SPECIAL_RAINBOW)

# ── Layout constants ────────────────────────────────────────────────
CELL = 68
BOARD_LEFT = 170
BOARD_TOP  = 100
WIN_W = 900
WIN_H = 700

# Gem palette — vibrant jewel colours
GEM_COLORS = [
    (230,  60,  60),   # 0 Ruby Red
    ( 60, 140, 230),   # 1 Sapphire Blue
    ( 55, 200,  80),   # 2 Emerald Green
    (240, 200,  40),   # 3 Topaz Yellow
    (180,  70, 220),   # 4 Amethyst Purple
    (240, 120,  40),   # 5 Amber Orange
]

SPECIAL_GLOW = {
    SPECIAL_HLINE:  (255, 255, 120),
    SPECIAL_VLINE:  (120, 255, 255),
    SPECIAL_BOMB:   (255, 160,  60),
    SPECIAL_RAINBOW:(255, 255, 255),
}

ICE_COLOR    = (160, 220, 255, 140)
STONE_COLOR  = (100, 100, 110)
CURSOR_COLOR = (255, 255,  60)
SELECT_COLOR = (255, 200,   0)

FONT_PATH = None   # use pygame default

# ── Particle ─────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x = x + random.uniform(-8, 8)
        self.y = y + random.uniform(-8, 8)
        angle = random.uniform(0, math.tau)
        speed = random.uniform(80, 260)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(40, 120)
        self.color = color
        self.life = random.uniform(0.4, 0.9)
        self.max_life = self.life
        self.r = random.uniform(3, 7)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400 * dt
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface):
        ratio = max(0, self.life / self.max_life)
        alpha = int(255 * ratio)
        r = max(1, int(self.r * ratio))
        color = (*self.color, alpha)
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (r, r), r)
        surface.blit(s, (int(self.x)-r, int(self.y)-r))


# ── Text helper ──────────────────────────────────────────────────────
_font_cache = {}

def get_font(size: int, bold=False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _font_cache:
        try:
            _font_cache[key] = pygame.font.SysFont('Arial', size, bold=bold)
        except Exception:
            _font_cache[key] = pygame.font.Font(None, size)
    return _font_cache[key]


def draw_text(surface, text, x, y, size=24, color=(255,255,255),
              bold=False, center=False, shadow=True):
    font = get_font(size, bold)
    if shadow:
        shadow_surf = font.render(text, True, (0,0,0))
        if center:
            sr = shadow_surf.get_rect(center=(x+2, y+2))
        else:
            sr = shadow_surf.get_rect(topleft=(x+2, y+2))
        surface.blit(shadow_surf, sr)
    surf = font.render(text, True, color)
    if center:
        r = surf.get_rect(center=(x, y))
    else:
        r = surf.get_rect(topleft=(x, y))
    surface.blit(surf, r)


# ── Gem drawing ──────────────────────────────────────────────────────
def _gem_surface(color_idx: int, special: int, size: int, t=0.0) -> pygame.Surface:
    """Create a gem surface with gradient + shine."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    base = GEM_COLORS[color_idx % len(GEM_COLORS)]
    radius = size // 2 - 2

    # Outer glow for special gems
    if special != SPECIAL_NONE:
        glow_col = SPECIAL_GLOW.get(special, (255,255,255))
        pulse = 0.7 + 0.3 * math.sin(t * 4)
        glow_r = int(radius * 1.3 * pulse)
        glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*glow_col, 60), (cx, cy), glow_r)
        s.blit(glow_surf, (0,0))

    # Body gradient (simulate with concentric circles)
    for i in range(radius, 0, -2):
        ratio = i / radius
        dark = tuple(max(0, int(c * 0.35)) for c in base)
        r = tuple(int(dark[j] + (base[j] - dark[j]) * (1 - ratio**1.5)) for j in range(3))
        pygame.draw.circle(s, r, (cx, cy), i)

    # Shine highlight
    shine_r = max(2, radius // 3)
    shine_x = cx - radius // 3
    shine_y = cy - radius // 3
    shine_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(shine_surf, (255,255,255,110), (shine_x, shine_y), shine_r)
    s.blit(shine_surf, (0,0))

    # Special marker
    if special == SPECIAL_HLINE:
        pygame.draw.line(s, (255,255,140), (2, cy), (size-2, cy), 3)
    elif special == SPECIAL_VLINE:
        pygame.draw.line(s, (140,255,255), (cx, 2), (cx, size-2), 3)
    elif special == SPECIAL_BOMB:
        pygame.draw.circle(s, (255,160,60), (cx, cy), radius//3)
    elif special == SPECIAL_RAINBOW:
        # small rainbow ring
        for i, col in enumerate(GEM_COLORS):
            angle = i * math.tau / len(GEM_COLORS)
            px = cx + int((radius//2) * math.cos(angle))
            py = cy + int((radius//2) * math.sin(angle))
            pygame.draw.circle(s, col, (px, py), 4)

    return s


# Cache gem surfaces per (color, special, size) to avoid re-rendering every frame
_gem_cache = {}

def get_gem_surf(color_idx, special, size, t=0.0):
    # Re-generate animated gems every frame; cache static ones
    if special != SPECIAL_NONE:
        return _gem_surface(color_idx, special, size, t)
    key = (color_idx, special, size)
    if key not in _gem_cache:
        _gem_cache[key] = _gem_surface(color_idx, special, size)
    return _gem_cache[key]


# ── Board cell position helpers ───────────────────────────────────────
def cell_to_pixel(r, c):
    """Top-left pixel of cell (r,c)."""
    return (BOARD_LEFT + c * CELL, BOARD_TOP + r * CELL)

def cell_center(r, c):
    x, y = cell_to_pixel(r, c)
    return (x + CELL//2, y + CELL//2)


# ── Main renderer class ───────────────────────────────────────────────
class Renderer:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.particles: list[Particle] = []
        self._bg_cache = {}

    # ── Particle helpers ──────────────────────────────────────────────
    def spawn_particles(self, r, c, color_idx, count=12):
        cx, cy = cell_center(r, c)
        color = GEM_COLORS[color_idx % len(GEM_COLORS)]
        for _ in range(count):
            self.particles.append(Particle(cx, cy, color))

    def update_particles(self, dt):
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update(dt)

    def draw_particles(self):
        for p in self.particles:
            p.draw(self.surface)

    # ── Background ────────────────────────────────────────────────────
    def draw_background(self, bg_color=(20,30,60), t=0.0):
        """Gradient background with subtle animated stars."""
        s = self.surface
        w, h = s.get_size()
        # Simple vertical gradient
        top = bg_color
        bot = tuple(max(0, c - 20) for c in bg_color)
        for y in range(h):
            ratio = y / h
            col = tuple(int(top[i] + (bot[i]-top[i])*ratio) for i in range(3))
            pygame.draw.line(s, col, (0, y), (w, y))

        # Twinkling stars
        rng = random.Random(42)
        for _ in range(60):
            sx = rng.randint(0, w)
            sy = rng.randint(0, h//2)
            brightness = int(128 + 127 * math.sin(t*1.5 + rng.uniform(0, math.tau)))
            pygame.draw.circle(s, (brightness,brightness,brightness), (sx, sy), 1)

    # ── Board background ──────────────────────────────────────────────
    def draw_board_bg(self):
        board_w = 8 * CELL
        board_h = 8 * CELL
        # Shadow
        shadow = pygame.Surface((board_w+16, board_h+16), pygame.SRCALPHA)
        shadow.fill((0,0,0,80))
        self.surface.blit(shadow, (BOARD_LEFT-8, BOARD_TOP-8))
        # Board panel
        panel = pygame.Surface((board_w, board_h), pygame.SRCALPHA)
        panel.fill((20,20,40,200))
        self.surface.blit(panel, (BOARD_LEFT, BOARD_TOP))
        # Cell grid
        for r in range(8):
            for c in range(8):
                x, y = cell_to_pixel(r, c)
                col = (35,35,60) if (r+c)%2==0 else (28,28,50)
                pygame.draw.rect(self.surface, col, (x+1, y+1, CELL-2, CELL-2))
        # Border
        pygame.draw.rect(self.surface, (80,80,130),
                         (BOARD_LEFT, BOARD_TOP, board_w, board_h), 2)

    # ── Obstacles ─────────────────────────────────────────────────────
    def draw_ice(self, r, c):
        x, y = cell_to_pixel(r, c)
        ice_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        ice_surf.fill(ICE_COLOR)
        # Grid lines on ice
        pygame.draw.rect(ice_surf, (200,240,255,180), (0,0,CELL,CELL), 2)
        self.surface.blit(ice_surf, (x, y))

    def draw_stone(self, r, c):
        x, y = cell_to_pixel(r, c)
        pygame.draw.rect(self.surface, STONE_COLOR, (x+2, y+2, CELL-4, CELL-4), border_radius=6)
        pygame.draw.rect(self.surface, (70,70,80), (x+2, y+2, CELL-4, CELL-4), 2, border_radius=6)

    # ── Gems ──────────────────────────────────────────────────────────
    def draw_gem(self, r, c, gem: Gem, t=0.0, cursor=False, selected=False):
        bx, by = cell_to_pixel(r, c)
        # Pixel position with animation offset
        px = bx + int(gem.anim_x * CELL)
        py = by + int(gem.anim_y * CELL)

        scale = gem.anim_scale
        size = max(4, int(CELL * scale))
        offset = (CELL - size) // 2

        surf = get_gem_surf(gem.color, gem.special, size, t)

        if gem.matched:
            # Flash white
            flash = pygame.Surface((size, size), pygame.SRCALPHA)
            flash.fill((255,255,255,int(128 * (0.5+0.5*math.sin(t*20)))))
            surf = surf.copy()
            surf.blit(flash, (0,0))

        self.surface.blit(surf, (px + offset, py + offset))

        # Selection ring
        if selected:
            pygame.draw.rect(self.surface, SELECT_COLOR,
                             (bx+2, by+2, CELL-4, CELL-4), 3, border_radius=8)
        elif cursor:
            pygame.draw.rect(self.surface, CURSOR_COLOR,
                             (bx+2, by+2, CELL-4, CELL-4), 2, border_radius=8)

    # ── Full board render ─────────────────────────────────────────────
    def draw_board(self, board: Board, cursor, selected, t=0.0):
        self.draw_board_bg()
        for r in range(board.rows):
            for c in range(board.cols):
                # Stone
                if board.locked[r][c]:
                    self.draw_stone(r, c)
                    continue
                gem = board.grid[r][c]
                if gem is None:
                    continue
                is_cursor  = (cursor == (r,c)) and selected is None
                is_selected= (selected == (r,c))
                self.draw_gem(r, c, gem, t, cursor=is_cursor, selected=is_selected)
                # Ice overlay on top
                if board.ice[r][c] > 0:
                    self.draw_ice(r, c)

    # ── HUD ───────────────────────────────────────────────────────────
    def draw_hud(self, level_num, score, score_goal, moves_left,
                 time_left, combo, description):
        s = self.surface
        # Left panel
        panel = pygame.Surface((160, WIN_H), pygame.SRCALPHA)
        panel.fill((10,10,25,200))
        s.blit(panel, (0, 0))

        draw_text(s, f'关卡 {level_num}', 80, 20, 28, (255,220,80), bold=True, center=True)
        draw_text(s, description, 80, 60, 14, (200,200,220), center=True)

        # Score
        draw_text(s, '得分', 80, 110, 18, (180,180,200), center=True)
        draw_text(s, str(score), 80, 135, 32, (255,255,100), bold=True, center=True)
        # Goal bar
        bar_w = 130
        filled = min(bar_w, int(bar_w * score / max(1, score_goal)))
        pygame.draw.rect(s, (40,40,60), (15, 175, bar_w, 14), border_radius=7)
        pygame.draw.rect(s, (80,220,100), (15, 175, filled, 14), border_radius=7)
        draw_text(s, f'目标: {score_goal}', 80, 194, 14, (160,200,160), center=True)

        # Moves or timer
        if moves_left is not None:
            draw_text(s, '剩余步数', 80, 240, 16, (180,180,200), center=True)
            col = (255,80,80) if moves_left <= 5 else (255,220,80)
            draw_text(s, str(moves_left), 80, 265, 44, col, bold=True, center=True)
        elif time_left is not None:
            draw_text(s, '剩余时间', 80, 240, 16, (180,180,200), center=True)
            col = (255,80,80) if time_left <= 10 else (80,200,255)
            draw_text(s, f'{int(time_left)}s', 80, 265, 44, col, bold=True, center=True)

        # Combo
        if combo > 1:
            draw_text(s, f'连击 ×{combo}!', 80, 330, 22, (255,140,0), bold=True, center=True)

        # Controls hint
        draw_text(s, '方向键:移动', 80, WIN_H-160, 13, (120,120,140), center=True)
        draw_text(s, '空格:选择/交换', 80, WIN_H-140, 13, (120,120,140), center=True)
        draw_text(s, 'H:提示', 80, WIN_H-120, 13, (120,120,140), center=True)
        draw_text(s, 'P:暂停', 80, WIN_H-100, 13, (120,120,140), center=True)
        draw_text(s, 'ESC:退出', 80, WIN_H-80, 13, (120,120,140), center=True)

    # ── Overlay screens ───────────────────────────────────────────────
    def draw_overlay(self, title, subtitle, color=(255,220,80)):
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,170))
        self.surface.blit(overlay, (0,0))
        draw_text(self.surface, title, WIN_W//2, WIN_H//2 - 50,
                  64, color, bold=True, center=True)
        draw_text(self.surface, subtitle, WIN_W//2, WIN_H//2 + 30,
                  28, (220,220,255), center=True)

    def draw_title_screen(self, t=0.0):
        self.draw_background((10,15,40), t)
        # Title
        pulse = 1.0 + 0.04 * math.sin(t * 2)
        title = '宝石消消乐'
        draw_text(self.surface, title, WIN_W//2, 180, int(72*pulse),
                  (255,215,0), bold=True, center=True, shadow=True)
        draw_text(self.surface, 'Match Three Gems', WIN_W//2, 260, 30,
                  (180,200,255), center=True)

        # Animated gems row
        for i, col in enumerate(GEM_COLORS):
            gx = WIN_W//2 - len(GEM_COLORS)*40 + i*80
            gy = 340
            offset_y = int(12 * math.sin(t*2 + i * 0.8))
            s2 = _gem_surface(i, SPECIAL_NONE, 60)
            self.surface.blit(s2, (gx-30, gy + offset_y))

        draw_text(self.surface, '按 Enter 开始游戏', WIN_W//2, 430,
                  26, (255,255,160), center=True, bold=True)
        draw_text(self.surface, '按 数字键 选择关卡 (1–9)', WIN_W//2, 475,
                  20, (160,160,200), center=True)
        draw_text(self.surface, '使用键盘方向键 + 空格键操作', WIN_W//2, 510,
                  18, (120,130,160), center=True)

        # Copyright
        draw_text(self.surface, '音乐来自 soundimage.org (CC 授权)',
                  WIN_W//2, WIN_H-30, 14, (80,80,100), center=True, shadow=False)

    def draw_level_complete(self, level_num, score, score_goal, bonus, t=0.0):
        self.draw_background((10,40,20), t)
        draw_text(self.surface, '关卡完成!', WIN_W//2, 160, 72,
                  (80,255,120), bold=True, center=True)
        draw_text(self.surface, f'第 {level_num} 关', WIN_W//2, 255, 36,
                  (200,255,200), center=True)
        draw_text(self.surface, f'得分: {score}', WIN_W//2, 310, 32,
                  (255,255,100), bold=True, center=True)
        if bonus > 0:
            draw_text(self.surface, f'额外奖励: +{bonus}', WIN_W//2, 360, 26,
                      (255,180,50), center=True)
        draw_text(self.surface, '按 Enter 进入下一关', WIN_W//2, 430, 26,
                  (160,255,160), center=True, bold=True)
        draw_text(self.surface, '按 ESC 返回标题', WIN_W//2, 470, 20,
                  (120,160,120), center=True)

    def draw_game_over(self, level_num, score, score_goal, t=0.0):
        self.draw_background((40,10,10), t)
        draw_text(self.surface, '挑战失败', WIN_W//2, 180, 72,
                  (255,80,80), bold=True, center=True)
        draw_text(self.surface, f'第 {level_num} 关', WIN_W//2, 268, 36,
                  (220,160,160), center=True)
        draw_text(self.surface, f'得分: {score} / 目标: {score_goal}',
                  WIN_W//2, 325, 26, (255,200,200), center=True)
        draw_text(self.surface, '按 Enter 重试', WIN_W//2, 400, 28,
                  (255,160,160), bold=True, center=True)
        draw_text(self.surface, '按 ESC 返回标题', WIN_W//2, 445, 20,
                  (160,120,120), center=True)

    def draw_paused(self):
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        self.surface.blit(overlay, (0,0))
        draw_text(self.surface, '游戏暂停', WIN_W//2, WIN_H//2 - 40,
                  60, (255,255,100), bold=True, center=True)
        draw_text(self.surface, '按 P 继续游戏', WIN_W//2, WIN_H//2 + 30,
                  26, (200,200,255), center=True)

    def draw_hint(self, pos1, pos2):
        for (r, c) in [pos1, pos2]:
            x, y = cell_to_pixel(r, c)
            pulse_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            pygame.draw.rect(pulse_surf, (255,255,0,100),
                             (0, 0, CELL, CELL), border_radius=8)
            pygame.draw.rect(pulse_surf, (255,255,0,200),
                             (0, 0, CELL, CELL), 3, border_radius=8)
            self.surface.blit(pulse_surf, (x, y))

    def draw_score_popup(self, r, c, points, t_shown, t=0.0):
        """Floating +score text."""
        cx, cy = cell_center(r, c)
        elapsed = t - t_shown
        if elapsed > 1.0:
            return
        alpha = int(255 * (1 - elapsed))
        cy_anim = cy - int(50 * elapsed)
        col = (255, 220, 50, alpha)
        surf = get_font(20, bold=True).render(f'+{points}', True, (255,220,50))
        surf.set_alpha(alpha)
        self.surface.blit(surf, surf.get_rect(center=(cx, cy_anim)))
