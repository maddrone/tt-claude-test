#!/usr/bin/env python3
"""
宝石消消乐 — Match-Three Puzzle Game
Run: python main.py
"""
import sys
import os

# Make sure assets dir exists
os.makedirs(os.path.join(os.path.dirname(__file__), 'assets', 'sounds'), exist_ok=True)

import pygame
from game import Game
from renderer import WIN_W, WIN_H


def main():
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()

    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption('宝石消消乐 — Match Three Gems')

    # Set a nice icon (colored circle)
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(icon, (220, 60, 60), (16, 16), 14)
    pygame.draw.circle(icon, (255,255,255,100), (10, 10), 6)
    pygame.display.set_icon(icon)

    game = Game(screen)

    try:
        game.run()
    except KeyboardInterrupt:
        pass

    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()
