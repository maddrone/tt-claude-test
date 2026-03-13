#!/bin/bash
# Setup script for 宝石消消乐
echo "=== 安装依赖 / Installing dependencies ==="
pip install pygame --upgrade

echo ""
echo "=== 启动游戏 / Starting game ==="
python main.py
