#!/usr/bin/env python3
"""Pattern 1: Minimal dots - colored circles with numbers only"""
import json, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

data = json.load(sys.stdin)

R = '\033[0m'
DIM = '\033[2m'
BOLD = '\033[1m'

def gradient(pct):
    if pct < 50:
        r = int(pct * 5.1)
        return f'\033[38;2;{r};200;80m'
    else:
        g = int(200 - (pct - 50) * 4)
        return f'\033[38;2;255;{max(g, 0)};60m'

def dot(pct):
    p = round(pct)
    return f'{gradient(pct)}●{R} {BOLD}{p}%{R}'

model = data.get('model', {}).get('display_name', 'Claude')
parts = [f'{BOLD}{model}{R}']

ctx = data.get('context_window', {}).get('used_percentage')
if ctx is not None:
    parts.append(f'ctx {dot(ctx)}')

five = data.get('rate_limits', {}).get('five_hour', {}).get('used_percentage')
if five is not None:
    parts.append(f'5h {dot(five)}')

week = data.get('rate_limits', {}).get('seven_day', {}).get('used_percentage')
if week is not None:
    parts.append(f'7d {dot(week)}')

print(f'  {DIM}·{R}  '.join(parts), end='')
