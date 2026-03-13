"""
Board logic: grid management, matching, falling, special gems.
"""
import random
from typing import List, Tuple, Optional, Set

# Gem types
EMPTY = -1
# Normal gem colors: 0-5
NUM_COLORS = 6

# Special gem flags (stored as color + offset)
SPECIAL_NONE   = 0
SPECIAL_HLINE  = 1   # horizontal line clear
SPECIAL_VLINE  = 2   # vertical line clear
SPECIAL_BOMB   = 3   # 3x3 clear
SPECIAL_RAINBOW= 4   # clears all of one color

ROWS = 8
COLS = 8


class Gem:
    def __init__(self, color: int, special: int = SPECIAL_NONE):
        self.color = color      # 0-5, or EMPTY
        self.special = special
        # Animation state
        self.anim_x = 0.0   # pixel offset from logical position
        self.anim_y = 0.0
        self.anim_scale = 1.0
        self.anim_alpha = 255
        self.falling = False
        self.matched = False

    def __repr__(self):
        return f"Gem({self.color},{self.special})"


class Board:
    def __init__(self, level_cfg: dict):
        self.rows = ROWS
        self.cols = COLS
        self.grid: List[List[Optional[Gem]]] = [[None]*self.cols for _ in range(self.rows)]
        self.locked: List[List[bool]] = [[False]*self.cols for _ in range(self.rows)]  # stone obstacles
        self.ice:    List[List[int]]  = [[0]*self.cols for _ in range(self.rows)]      # ice layers
        self.num_colors = level_cfg.get('num_colors', 5)
        self.selected: Optional[Tuple[int,int]] = None
        self.swap_pair: Optional[Tuple[Tuple[int,int], Tuple[int,int]]] = None
        self._fill_board()
        self._apply_obstacles(level_cfg)

    def _random_gem(self) -> Gem:
        return Gem(random.randint(0, self.num_colors - 1))

    def _fill_board(self):
        for r in range(self.rows):
            for c in range(self.cols):
                gem = self._random_gem()
                self.grid[r][c] = gem
        # Eliminate starting matches
        for _ in range(100):
            if not self._find_matches():
                break
            self._shuffle_no_match()

    def _shuffle_no_match(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.locked[r][c]:
                    self.grid[r][c] = self._random_gem()

    def _apply_obstacles(self, cfg: dict):
        ice_positions = cfg.get('ice', [])
        stone_positions = cfg.get('stones', [])
        for (r, c) in ice_positions:
            if 0 <= r < self.rows and 0 <= c < self.cols:
                self.ice[r][c] = 1
        for (r, c) in stone_positions:
            if 0 <= r < self.rows and 0 <= c < self.cols:
                self.locked[r][c] = True
                self.grid[r][c] = None

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------
    def _find_matches(self) -> List[Set[Tuple[int,int]]]:
        """Return list of match groups (sets of (r,c))."""
        visited = set()
        groups = []

        def color_at(r, c):
            g = self.grid[r][c]
            return g.color if g and g.color != EMPTY else EMPTY

        # Horizontal
        for r in range(self.rows):
            c = 0
            while c < self.cols:
                color = color_at(r, c)
                if color == EMPTY:
                    c += 1
                    continue
                run = [(r, c)]
                while c + len(run) < self.cols and color_at(r, c + len(run)) == color:
                    run.append((r, c + len(run)))
                if len(run) >= 3:
                    groups.append(set(run))
                c += len(run)

        # Vertical
        for c in range(self.cols):
            r = 0
            while r < self.rows:
                color = color_at(r, c)
                if color == EMPTY:
                    r += 1
                    continue
                run = [(r, c)]
                while r + len(run) < self.rows and color_at(r + len(run), c) == color:
                    run.append((r + len(run), c))
                if len(run) >= 3:
                    groups.append(set(run))
                r += len(run)

        # Merge overlapping groups
        merged = []
        for g in groups:
            found = False
            for m in merged:
                if m & g:
                    m |= g
                    found = True
                    break
            if not found:
                merged.append(g)
        return merged

    def find_and_mark_matches(self) -> List[Set[Tuple[int,int]]]:
        groups = self._find_matches()
        for group in groups:
            for (r, c) in group:
                if self.grid[r][c]:
                    self.grid[r][c].matched = True
        return groups

    def determine_special(self, group: Set[Tuple[int,int]], swap_pos: Optional[Tuple[int,int]]) -> Optional[int]:
        """Determine what special gem to create based on match size."""
        size = len(group)
        if size == 4:
            # Which direction was the match?
            rows_in_group = set(r for r, c in group)
            cols_in_group = set(c for r, c in group)
            if len(rows_in_group) == 1:
                return SPECIAL_HLINE
            else:
                return SPECIAL_VLINE
        elif size == 5:
            return SPECIAL_RAINBOW
        elif size >= 6:
            return SPECIAL_BOMB
        return None

    def clear_matches(self, groups: List[Set[Tuple[int,int]]], swap_pos=None) -> Tuple[int, List[Tuple[int,int,int]]]:
        """
        Remove matched gems, create specials.
        Returns (score_earned, list_of_cleared_positions_with_color).
        """
        score = 0
        cleared = []

        for group in groups:
            size = len(group)
            special = self.determine_special(group, swap_pos)
            base_score = {3: 60, 4: 120, 5: 200}.get(min(size, 5), 300)
            score += base_score * size

            # Find anchor position (swap target if available, else first)
            anchor = swap_pos if swap_pos in group else next(iter(group))

            for (r, c) in group:
                gem = self.grid[r][c]
                if gem:
                    cleared.append((r, c, gem.color))
                    # Break ice
                    if self.ice[r][c] > 0:
                        self.ice[r][c] -= 1
                        if self.ice[r][c] > 0:
                            continue  # Don't remove gem, just chip ice
                    self.grid[r][c] = None

            # Place special gem at anchor
            if special is not None and not self.locked[anchor[0]][anchor[1]]:
                anchor_color = cleared[-1][2] if cleared else 0
                # Get color from group
                for r, c, col in cleared:
                    if (r, c) == anchor:
                        anchor_color = col
                        break
                self.grid[anchor[0]][anchor[1]] = Gem(anchor_color, special)

        return score, cleared

    def activate_special(self, r: int, c: int) -> List[Tuple[int,int]]:
        """Activate a special gem, return positions cleared."""
        gem = self.grid[r][c]
        if not gem or gem.special == SPECIAL_NONE:
            return []

        positions = []
        if gem.special == SPECIAL_HLINE:
            positions = [(r, cc) for cc in range(self.cols)]
        elif gem.special == SPECIAL_VLINE:
            positions = [(rr, c) for rr in range(self.rows)]
        elif gem.special == SPECIAL_BOMB:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        positions.append((nr, nc))
        elif gem.special == SPECIAL_RAINBOW:
            target_color = gem.color
            positions = [(rr, cc) for rr in range(self.rows) for cc in range(self.cols)
                         if self.grid[rr][cc] and self.grid[rr][cc].color == target_color]

        for (pr, pc) in positions:
            if not self.locked[pr][pc]:
                if self.ice[pr][pc] > 0:
                    self.ice[pr][pc] -= 1
                else:
                    self.grid[pr][pc] = None
        return positions

    # ------------------------------------------------------------------
    # Falling / refilling
    # ------------------------------------------------------------------
    def apply_gravity(self) -> bool:
        """Drop gems down. Returns True if any gem moved."""
        moved = False
        for c in range(self.cols):
            for r in range(self.rows - 1, -1, -1):
                if self.grid[r][c] is None and not self.locked[r][c]:
                    # Find gem above
                    for rr in range(r - 1, -1, -1):
                        if self.grid[rr][c] is not None:
                            self.grid[r][c] = self.grid[rr][c]
                            self.grid[r][c].anim_y = -(r - rr) * 1.0  # start above
                            self.grid[r][c].falling = True
                            self.grid[rr][c] = None
                            moved = True
                            break
        return moved

    def fill_empty(self) -> List[Tuple[int,int]]:
        """Fill empty non-locked cells with new gems from top."""
        new_positions = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] is None and not self.locked[r][c]:
                    self.grid[r][c] = self._random_gem()
                    self.grid[r][c].anim_y = -float(r + 1)
                    self.grid[r][c].falling = True
                    new_positions.append((r, c))
        return new_positions

    # ------------------------------------------------------------------
    # Swap
    # ------------------------------------------------------------------
    def swap(self, r1: int, c1: int, r2: int, c2: int):
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]

    def has_match_after_swap(self, r1, c1, r2, c2) -> bool:
        self.swap(r1, c1, r2, c2)
        matches = self._find_matches()
        self.swap(r1, c1, r2, c2)
        return len(matches) > 0

    def is_adjacent(self, r1, c1, r2, c2) -> bool:
        return abs(r1 - r2) + abs(c1 - c2) == 1

    # ------------------------------------------------------------------
    # Hints / deadlock
    # ------------------------------------------------------------------
    def find_hint(self) -> Optional[Tuple[Tuple[int,int], Tuple[int,int]]]:
        """Find any valid swap."""
        for r in range(self.rows):
            for c in range(self.cols):
                for dr, dc in [(0,1),(1,0)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if not self.locked[r][c] and not self.locked[nr][nc]:
                            if self.has_match_after_swap(r, c, nr, nc):
                                return ((r, c), (nr, nc))
        return None

    def has_moves(self) -> bool:
        return self.find_hint() is not None

    # ------------------------------------------------------------------
    # Shuffle
    # ------------------------------------------------------------------
    def shuffle(self):
        gems = [self.grid[r][c] for r in range(self.rows) for c in range(self.cols)
                if self.grid[r][c] and not self.locked[r][c]]
        random.shuffle(gems)
        idx = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.locked[r][c]:
                    self.grid[r][c] = gems[idx] if idx < len(gems) else self._random_gem()
                    idx += 1
