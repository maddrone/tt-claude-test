"""
Level definitions — 25 levels with increasing difficulty.
Each level dict:
  num_colors  : how many gem colors on board
  moves       : allowed swaps (None = unlimited / time-based)
  time_limit  : seconds (None = no limit)
  score_goal  : score needed to pass
  ice         : list of (r,c) positions covered by ice
  stones      : list of (r,c) locked/empty cells
  ice_goal    : total ice cells to clear (overrides auto-count)
  description : short hint text
  bg_color    : (R,G,B) background tint
"""

LEVELS = [
    # ── Beginner ──────────────────────────────────────────────────────
    {   # 1
        'num_colors': 4, 'moves': 30, 'time_limit': None,
        'score_goal': 500, 'ice': [], 'stones': [],
        'description': '消除宝石获得500分！',
        'bg_color': (20, 30, 60),
    },
    {   # 2
        'num_colors': 4, 'moves': 28, 'time_limit': None,
        'score_goal': 800, 'ice': [], 'stones': [],
        'description': '获得800分过关！',
        'bg_color': (25, 35, 65),
    },
    {   # 3
        'num_colors': 4, 'moves': 25, 'time_limit': None,
        'score_goal': 1200, 'ice': [], 'stones': [],
        'description': '连击加分！目标1200分',
        'bg_color': (20, 40, 70),
    },
    {   # 4
        'num_colors': 5, 'moves': 25, 'time_limit': None,
        'score_goal': 1500, 'ice': [], 'stones': [],
        'description': '5种宝石，目标1500分',
        'bg_color': (30, 25, 70),
    },
    {   # 5
        'num_colors': 5, 'moves': 22, 'time_limit': None,
        'score_goal': 2000, 'ice': [], 'stones': [],
        'description': '更少步数，需要策略！',
        'bg_color': (35, 20, 65),
    },

    # ── Intermediate ──────────────────────────────────────────────────
    {   # 6
        'num_colors': 5, 'moves': 20, 'time_limit': None,
        'score_goal': 2500,
        'ice': [(3,3),(3,4),(4,3),(4,4)],
        'stones': [],
        'description': '打破冰块！',
        'bg_color': (15, 45, 80),
    },
    {   # 7
        'num_colors': 5, 'moves': 20, 'time_limit': None,
        'score_goal': 2800,
        'ice': [(2,2),(2,5),(5,2),(5,5),(3,3),(3,4),(4,3),(4,4)],
        'stones': [],
        'description': '更多冰块要清除',
        'bg_color': (10, 50, 85),
    },
    {   # 8
        'num_colors': 5, 'moves': 18, 'time_limit': None,
        'score_goal': 3200,
        'ice': [(r,c) for r in range(3,6) for c in range(2,6)],
        'stones': [],
        'description': '大片冰块，加油！',
        'bg_color': (10, 55, 90),
    },
    {   # 9
        'num_colors': 5, 'moves': 18, 'time_limit': None,
        'score_goal': 3600,
        'ice': [(0,c) for c in range(8)] + [(7,c) for c in range(8)],
        'stones': [],
        'description': '上下冰层，突破重围！',
        'bg_color': (15, 60, 90),
    },
    {   # 10
        'num_colors': 6, 'moves': 20, 'time_limit': None,
        'score_goal': 4000,
        'ice': [(r,c) for r in range(2,6) for c in range(1,7) if (r+c)%2==0],
        'stones': [],
        'description': '6种宝石登场！',
        'bg_color': (60, 20, 80),
    },

    # ── Advanced ──────────────────────────────────────────────────────
    {   # 11
        'num_colors': 5, 'moves': 20, 'time_limit': None,
        'score_goal': 4500,
        'ice': [],
        'stones': [(3,0),(3,7),(4,0),(4,7)],
        'description': '有障碍物，绕路消除',
        'bg_color': (70, 30, 20),
    },
    {   # 12
        'num_colors': 5, 'moves': 20, 'time_limit': None,
        'score_goal': 5000,
        'ice': [(2,3),(2,4),(5,3),(5,4)],
        'stones': [(0,3),(0,4),(7,3),(7,4)],
        'description': '冰块与障碍并存！',
        'bg_color': (75, 25, 25),
    },
    {   # 13
        'num_colors': 6, 'moves': 18, 'time_limit': None,
        'score_goal': 5500,
        'ice': [(r,c) for r in range(1,7) for c in range(1,7) if r==1 or r==6 or c==1 or c==6],
        'stones': [(0,0),(0,7),(7,0),(7,7)],
        'description': '冰环包围，内外夹击！',
        'bg_color': (80, 20, 30),
    },
    {   # 14
        'num_colors': 6, 'moves': 16, 'time_limit': None,
        'score_goal': 6000,
        'ice': [(3,2),(3,3),(3,4),(3,5),(4,2),(4,3),(4,4),(4,5)],
        'stones': [(0,2),(0,5),(7,2),(7,5),(3,0),(4,0),(3,7),(4,7)],
        'description': '步步为营，精准消除',
        'bg_color': (85, 15, 35),
    },
    {   # 15 — first timed
        'num_colors': 5, 'moves': None, 'time_limit': 60,
        'score_goal': 5000,
        'ice': [],
        'stones': [(3,3),(3,4),(4,3),(4,4)],
        'description': '60秒限时挑战！',
        'bg_color': (80, 50, 10),
    },

    # ── Expert ────────────────────────────────────────────────────────
    {   # 16
        'num_colors': 6, 'moves': None, 'time_limit': 90,
        'score_goal': 8000,
        'ice': [(r,c) for r in range(2,6) for c in range(2,6)],
        'stones': [],
        'description': '90秒，达到8000分！',
        'bg_color': (20, 70, 50),
    },
    {   # 17
        'num_colors': 6, 'moves': 15, 'time_limit': None,
        'score_goal': 7000,
        'ice': [(r, c) for r in range(8) for c in range(8) if (r+c)%3==0],
        'stones': [(r, c) for r in range(8) for c in range(8) if (r+c)%5==0 and r>0 and c>0],
        'description': '棋盘充满挑战！',
        'bg_color': (20, 20, 80),
    },
    {   # 18
        'num_colors': 6, 'moves': 14, 'time_limit': None,
        'score_goal': 8000,
        'ice': [(r,c) for r in [0,1,6,7] for c in range(8)],
        'stones': [(r,c) for r in [3,4] for c in [0,1,6,7]],
        'description': '上下被冻，中间突破！',
        'bg_color': (50, 15, 75),
    },
    {   # 19
        'num_colors': 6, 'moves': None, 'time_limit': 75,
        'score_goal': 10000,
        'ice': [(r,c) for r in range(8) for c in range(8) if r%2==0],
        'stones': [],
        'description': '75秒，万分挑战！',
        'bg_color': (30, 70, 20),
    },
    {   # 20
        'num_colors': 6, 'moves': 20, 'time_limit': None,
        'score_goal': 9000,
        'ice': [(r,c) for r in range(8) for c in range(8) if (r*8+c)%2==0],
        'stones': [(r,c) for r in range(8) for c in range(8) if r in [3,4] and c in [3,4]],
        'description': '棋盘格冰，终极考验！',
        'bg_color': (60, 10, 60),
    },

    # ── Master ────────────────────────────────────────────────────────
    {   # 21
        'num_colors': 6, 'moves': 12, 'time_limit': None,
        'score_goal': 10000,
        'ice': [(r,c) for r in range(8) for c in range(4)],
        'stones': [(r,4) for r in range(8)],
        'description': '半边冻结，12步通关！',
        'bg_color': (70, 10, 40),
    },
    {   # 22
        'num_colors': 6, 'moves': None, 'time_limit': 60,
        'score_goal': 12000,
        'ice': [(r,c) for r in range(8) for c in range(8) if r!=4 and c!=4],
        'stones': [],
        'description': '60秒，12000分！爆炸吧！',
        'bg_color': (80, 5, 20),
    },
    {   # 23
        'num_colors': 6, 'moves': 18, 'time_limit': None,
        'score_goal': 11000,
        'ice': [(r,c) for r in range(8) for c in range(8) if abs(r-3.5)+abs(c-3.5)<4],
        'stones': [(0,0),(0,7),(7,0),(7,7)],
        'description': '菱形冰阵，突破中心！',
        'bg_color': (10, 50, 80),
    },
    {   # 24
        'num_colors': 6, 'moves': 10, 'time_limit': None,
        'score_goal': 12000,
        'ice': [(r,c) for r in range(8) for c in range(8)],
        'stones': [],
        'description': '全冰封！仅10步，传奇挑战！',
        'bg_color': (5, 40, 90),
    },
    {   # 25
        'num_colors': 6, 'moves': None, 'time_limit': 45,
        'score_goal': 15000,
        'ice': [(r,c) for r in range(8) for c in range(8)],
        'stones': [],
        'description': '45秒全冰封，15000分！终极宗师！',
        'bg_color': (50, 0, 50),
    },
]


def get_level(n: int) -> dict:
    """Return level config (1-indexed). Repeats last for n > len."""
    if n < 1:
        n = 1
    if n > len(LEVELS):
        # Generate harder infinite levels
        base = LEVELS[-1].copy()
        extra = n - len(LEVELS)
        base['score_goal'] = 15000 + extra * 2000
        base['moves'] = max(8, 10 - extra // 3) if base['moves'] else None
        base['time_limit'] = max(30, 45 - extra * 3) if base['time_limit'] else None
        base['description'] = f'第{n}关：无尽挑战！'
        return base
    return LEVELS[n - 1]
