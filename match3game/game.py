"""
Game state machine and main loop logic.
States: TITLE → PLAYING → PAUSED → LEVEL_COMPLETE → GAME_OVER
"""
import pygame
import time
from board import Board, SPECIAL_NONE
from levels import get_level
from renderer import Renderer, WIN_W, WIN_H, cell_to_pixel, CELL
from audio import AudioManager

MUSIC_END_EVENT = pygame.USEREVENT + 1

# Animation durations (seconds)
SWAP_ANIM     = 0.12
FALL_ANIM     = 0.18
MATCH_ANIM    = 0.15
HINT_SHOW     = 2.5

# States
TITLE          = 'title'
PLAYING        = 'playing'
PAUSED         = 'paused'
LEVEL_COMPLETE = 'level_complete'
GAME_OVER      = 'game_over'

# Phases within PLAYING
PH_INPUT    = 'input'
PH_SWAP     = 'swap'
PH_MATCH    = 'match'
PH_FALL     = 'fall'
PH_REFILL   = 'refill'
PH_CHECK    = 'check'


class ScorePopup:
    def __init__(self, r, c, points, t):
        self.r, self.c = r, c
        self.points = points
        self.t_born = t


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.renderer = Renderer(screen)
        self.audio = AudioManager()
        self.audio.init()
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)

        self.state = TITLE
        self.level_num = 1
        self.clock = pygame.time.Clock()
        self.t = 0.0   # global time

        # Playing state
        self.board: Board = None
        self.level_cfg: dict = {}
        self.score = 0
        self.moves_used = 0
        self.combo = 0
        self.phase = PH_INPUT
        self.cursor = (3, 3)
        self.selected = None
        self.phase_timer = 0.0
        self.hint_pair = None
        self.hint_timer = 0.0
        self.popups: list[ScorePopup] = []
        self.time_remaining = None

        # Swap animation data
        self._swap_a = None
        self._swap_b = None
        self._swap_valid = False

    # ── Start level ───────────────────────────────────────────────────
    def start_level(self, n: int):
        self.level_num = n
        self.level_cfg = get_level(n)
        self.board = Board(self.level_cfg)
        self.score = 0
        self.moves_used = 0
        self.combo = 0
        self.phase = PH_INPUT
        self.cursor = (3, 3)
        self.selected = None
        self.hint_pair = None
        self.hint_timer = 0.0
        self.popups = []
        self.time_remaining = self.level_cfg.get('time_limit')
        self.state = PLAYING

    @property
    def moves_left(self):
        max_moves = self.level_cfg.get('moves')
        if max_moves is None:
            return None
        return max(0, max_moves - self.moves_used)

    def _out_of_resources(self):
        ml = self.moves_left
        if ml is not None and ml <= 0:
            return True
        if self.time_remaining is not None and self.time_remaining <= 0:
            return True
        return False

    # ── Main run ──────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.05)
            self.t += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == MUSIC_END_EVENT:
                    self.audio.on_music_end()
                self._handle_event(event)

            self._update(dt)
            self._draw()
            pygame.display.flip()

    # ── Event handling ────────────────────────────────────────────────
    def _handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        key = event.key

        if self.state == TITLE:
            if key == pygame.K_RETURN or key == pygame.K_SPACE:
                self.start_level(self.level_num)
            elif pygame.K_1 <= key <= pygame.K_9:
                self.start_level(key - pygame.K_0)
            elif key == pygame.K_0:
                self.start_level(10)

        elif self.state == PLAYING:
            if key == pygame.K_ESCAPE:
                self.state = TITLE
            elif key == pygame.K_p:
                self.state = PAUSED
            elif key == pygame.K_m:
                self.audio.toggle_music()
            elif self.phase == PH_INPUT:
                self._handle_play_input(key)

        elif self.state == PAUSED:
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = PLAYING

        elif self.state == LEVEL_COMPLETE:
            if key == pygame.K_RETURN or key == pygame.K_SPACE:
                self.start_level(self.level_num + 1)
            elif key == pygame.K_ESCAPE:
                self.state = TITLE

        elif self.state == GAME_OVER:
            if key == pygame.K_RETURN or key == pygame.K_SPACE:
                self.start_level(self.level_num)
            elif key == pygame.K_ESCAPE:
                self.state = TITLE

    def _handle_play_input(self, key):
        r, c = self.cursor
        if key == pygame.K_UP:
            self.cursor = (max(0, r-1), c)
        elif key == pygame.K_DOWN:
            self.cursor = (min(7, r+1), c)
        elif key == pygame.K_LEFT:
            self.cursor = (r, max(0, c-1))
        elif key == pygame.K_RIGHT:
            self.cursor = (r, min(7, c+1))
        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            self._on_select()
        elif key == pygame.K_h:
            self._show_hint()
        elif key == pygame.K_ESCAPE:
            self.selected = None

    def _on_select(self):
        r, c = self.cursor
        if self.board.locked[r][c]:
            return
        if self.selected is None:
            # First selection
            if self.board.grid[r][c] is not None:
                self.selected = (r, c)
                self.audio.play('select', 0.5)
        else:
            sr, sc = self.selected
            if (r, c) == (sr, sc):
                self.selected = None
                return
            if self.board.is_adjacent(sr, sc, r, c):
                self._begin_swap(sr, sc, r, c)
            else:
                # Move selection to new cell
                self.selected = (r, c)
                self.audio.play('select', 0.4)

    def _begin_swap(self, r1, c1, r2, c2):
        valid = self.board.has_match_after_swap(r1, c1, r2, c2)
        # Also allow swapping special gems regardless
        g1 = self.board.grid[r1][c1]
        g2 = self.board.grid[r2][c2]
        special_swap = (g1 and g1.special != SPECIAL_NONE) or \
                       (g2 and g2.special != SPECIAL_NONE)
        if not valid and not special_swap:
            self.audio.play('invalid', 0.4)
            self.selected = None
            return

        self._swap_a = (r1, c1)
        self._swap_b = (r2, c2)
        self._swap_valid = True
        self.audio.play('swap', 0.5)
        self.selected = None
        self.phase = PH_SWAP
        self.phase_timer = 0.0
        # Animate: set anim offsets
        dr, dc = r2-r1, c2-c1
        self.board.grid[r1][c1].anim_x = 0.0
        self.board.grid[r1][c1].anim_y = 0.0
        if self.board.grid[r2][c2]:
            self.board.grid[r2][c2].anim_x = 0.0
            self.board.grid[r2][c2].anim_y = 0.0

    def _show_hint(self):
        hint = self.board.find_hint()
        self.hint_pair = hint
        self.hint_timer = self.t

    # ── Update ────────────────────────────────────────────────────────
    def _update(self, dt):
        if self.state == TITLE:
            return
        if self.state in (PAUSED, LEVEL_COMPLETE, GAME_OVER):
            return

        # Update timer
        if self.time_remaining is not None and self.phase == PH_INPUT:
            self.time_remaining = max(0.0, self.time_remaining - dt)

        self.renderer.update_particles(dt)

        if self.phase == PH_SWAP:
            self._update_swap(dt)
        elif self.phase == PH_MATCH:
            self._update_match(dt)
        elif self.phase == PH_FALL:
            self._update_fall(dt)
        elif self.phase == PH_CHECK:
            self._update_check()
        elif self.phase == PH_INPUT:
            self._update_input_phase()

        # Clean up old popups
        self.popups = [p for p in self.popups if self.t - p.t_born < 1.2]

    def _update_input_phase(self):
        if self._out_of_resources():
            if self.score >= self.level_cfg['score_goal']:
                self._complete_level()
            else:
                self.audio.play('game_over')
                self.state = GAME_OVER

    def _update_swap(self, dt):
        self.phase_timer += dt
        ratio = min(1.0, self.phase_timer / SWAP_ANIM)
        r1, c1 = self._swap_a
        r2, c2 = self._swap_b
        dr, dc = r2-r1, c2-c1
        g1 = self.board.grid[r1][c1]
        g2 = self.board.grid[r2][c2]
        if g1:
            g1.anim_x = dc * ratio
            g1.anim_y = dr * ratio
        if g2:
            g2.anim_x = -dc * ratio
            g2.anim_y = -dr * ratio

        if ratio >= 1.0:
            if g1: g1.anim_x = g1.anim_y = 0
            if g2: g2.anim_x = g2.anim_y = 0
            self.board.swap(r1, c1, r2, c2)
            self.moves_used += 1
            # Check for specials
            new_g1 = self.board.grid[r1][c1]
            new_g2 = self.board.grid[r2][c2]
            special_activated = False
            for (gr, gc), gem in [((r1,c1), new_g1), ((r2,c2), new_g2)]:
                if gem and gem.special != SPECIAL_NONE:
                    positions = self.board.activate_special(gr, gc)
                    for (pr, pc) in positions:
                        self.renderer.spawn_particles(pr, pc, 0)
                    self.audio.play('special')
                    special_activated = True
            self.phase = PH_MATCH
            self.phase_timer = 0.0
            self.combo = 0

    def _update_match(self, dt):
        self.phase_timer += dt
        if self.phase_timer < MATCH_ANIM:
            # Animate matched gems (scale down)
            for r in range(8):
                for c in range(8):
                    g = self.board.grid[r][c]
                    if g and g.matched:
                        g.anim_scale = max(0.0, 1.0 - self.phase_timer / MATCH_ANIM)
            return

        groups = self.board.find_and_mark_matches()
        if not groups:
            # No matches — check if valid swap happened
            if self.combo == 0:
                # Reverse the swap
                r1, c1 = self._swap_a
                r2, c2 = self._swap_b
                self.board.swap(r1, c1, r2, c2)
                self.moves_used -= 1
                self.audio.play('invalid', 0.4)
            self.phase = PH_INPUT
            return

        self.combo += 1
        # Score
        score_earned, cleared = self.board.clear_matches(groups, swap_pos=self._swap_b)
        combo_mult = min(self.combo, 6)
        score_earned = int(score_earned * (1 + 0.25 * (combo_mult - 1)))
        self.score += score_earned

        # Particles and audio
        for (r, c, color_idx) in cleared:
            self.renderer.spawn_particles(r, c, color_idx, count=8)

        if self.combo > 1:
            self.audio.play('combo')
        else:
            self.audio.play('match')

        # Score popup at center of biggest group
        biggest = max(groups, key=len)
        rs = [r for r, c in biggest]
        cs = [c for r, c in biggest]
        mr = sum(rs)//len(rs)
        mc = sum(cs)//len(cs)
        self.popups.append(ScorePopup(mr, mc, score_earned, self.t))

        # Reset scales
        for r in range(8):
            for c in range(8):
                g = self.board.grid[r][c]
                if g:
                    g.anim_scale = 1.0
                    g.matched = False

        self.phase = PH_FALL
        self.phase_timer = 0.0

        # Check win condition mid-play
        if self.score >= self.level_cfg['score_goal']:
            if self.level_cfg.get('moves') is None and self.level_cfg.get('time_limit') is None:
                self._complete_level()

    def _update_fall(self, dt):
        self.phase_timer += dt
        ratio = min(1.0, self.phase_timer / FALL_ANIM)
        # Animate falling gems
        for r in range(8):
            for c in range(8):
                g = self.board.grid[r][c]
                if g and g.falling:
                    g.anim_y = g.anim_y * (1.0 - ratio * 0.4)
                    if abs(g.anim_y) < 0.02:
                        g.anim_y = 0.0
                        g.falling = False

        if ratio >= 1.0:
            # Apply gravity step and refill
            still_falling = self.board.apply_gravity()
            self.board.fill_empty()
            if still_falling:
                self.phase_timer = 0.0  # keep animating
            else:
                # All settled — check for chain matches
                self.phase = PH_MATCH
                self.phase_timer = 0.0

    def _update_check(self):
        if not self.board.has_moves():
            self.board.shuffle()
        self.phase = PH_INPUT

    def _complete_level(self):
        # Bonus for remaining moves/time
        bonus = 0
        ml = self.moves_left
        if ml is not None:
            bonus = ml * 30
        elif self.time_remaining is not None:
            bonus = int(self.time_remaining) * 20
        self.score += bonus
        self.audio.play('level_complete')
        self.state = LEVEL_COMPLETE

    # ── Draw ──────────────────────────────────────────────────────────
    def _draw(self):
        r = self.renderer
        if self.state == TITLE:
            r.draw_title_screen(self.t)
            return

        cfg = self.level_cfg

        # Background
        r.draw_background(cfg.get('bg_color', (20,30,60)), self.t)

        if self.state in (PLAYING, PAUSED):
            r.draw_board(self.board, self.cursor,
                         self.selected if self.phase == PH_INPUT else None,
                         self.t)
            r.draw_particles()
            # Hint
            if self.hint_pair and (self.t - self.hint_timer) < HINT_SHOW:
                r.draw_hint(*self.hint_pair)
            # Score popups
            for p in self.popups:
                r.draw_score_popup(p.r, p.c, p.points, p.t_born, self.t)
            # HUD
            r.draw_hud(
                self.level_num, self.score,
                cfg['score_goal'], self.moves_left,
                self.time_remaining, self.combo,
                cfg.get('description', ''),
            )
            if self.state == PAUSED:
                r.draw_paused()

        elif self.state == LEVEL_COMPLETE:
            ml = self.moves_left or 0
            tr = self.time_remaining or 0
            bonus = ml * 30 if self.level_cfg.get('moves') else int(tr) * 20
            r.draw_level_complete(self.level_num, self.score,
                                   cfg['score_goal'], bonus, self.t)

        elif self.state == GAME_OVER:
            r.draw_game_over(self.level_num, self.score,
                              cfg['score_goal'], self.t)
