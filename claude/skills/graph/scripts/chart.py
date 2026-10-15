#!/usr/bin/env python3
"""ざっくりCLIグラフ。標準ライブラリのみで動く ASCII/Unicode チャート。

    chart.py bar  [file] [options]
    chart.py line [file] [options]

データはファイルか標準入力から読む。1行1レコード。
区切りは タブ > カンマ > 空白 の順に自動判定（空白の場合は行末から続く
数値をすべて値とみなし、残りをラベルにするのでラベルに空白があってもよい）。

    8/13 迎え盆<TAB>579<TAB>374

1行目の2列目が数値でなければヘッダ行として系列名に使う。
値が空・"-"・"NA" の場合は欠損として棒を描かない。
"""

import argparse
import re
import sys
import unicodedata

BLOCKS = " ▏▎▍▌▋▊▉█"          # 1/8 刻みの部分ブロック
FILLS = ["█", "▒", "▓", "░"]   # 系列ごとの塗り分け（色を使わない代わり）
MARKS = ["●", "○", "◆", "+"]   # 折れ線の点
MISSING = {"", "-", "na", "n/a", "null", "none"}


def disp_width(s):
    """全角を2桁として数えた表示幅。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, width, align="left"):
    gap = max(0, width - disp_width(s))
    return s + " " * gap if align == "left" else " " * gap + s


def clip(s, width):
    """表示幅 width に収まるよう末尾を削る。"""
    if disp_width(s) <= width:
        return s
    out = ""
    for c in s:
        if disp_width(out + c) > width:
            break
        out += c
    return out


def to_num(tok):
    tok = tok.strip().replace(",", "").replace("%", "")
    if tok.lower() in MISSING:
        return None
    try:
        return float(tok)
    except ValueError:
        raise ValueError(f"数値として読めません: {tok!r}")


def is_num(tok):
    try:
        return to_num(tok) is not None
    except ValueError:
        return False


def split_line(line, delim):
    if delim:
        return [f.strip() for f in line.split(delim)]
    # 空白区切り: 行末から続く数値トークンを値、残りをラベルとする
    toks = line.split()
    i = len(toks)
    while i > 1 and is_num(toks[i - 1]):
        i -= 1
    return [" ".join(toks[:i])] + toks[i:]


def parse(text):
    """-> (labels, series_names, rows)  rows[i] = [値 or None, ...]"""
    lines = [ln.rstrip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        sys.exit("chart.py: データが空です")

    delim = "\t" if "\t" in lines[0] else ("," if "," in lines[0] else None)

    table = [split_line(ln, delim) for ln in lines]
    table = [r for r in table if len(r) >= 2]
    if not table:
        sys.exit("chart.py: 『ラベル 値』の形式の行がありません")

    names = None
    if not is_num(table[0][1]):
        names = table[0][1:]
        table = table[1:]
        if not table:
            sys.exit("chart.py: ヘッダ行しかありません")
        if len(names) == 1:
            # 1系列だとヘッダか「値が壊れたデータ行」か区別できないので知らせる
            print(f"chart.py: 1行目をヘッダとみなしました（系列名 {names[0]!r}）",
                  file=sys.stderr)

    ncol = max(len(r) for r in table) - 1
    labels, rows = [], []
    for r in table:
        labels.append(r[0])
        vals = [to_num(v) for v in r[1:]]
        vals += [None] * (ncol - len(vals))
        rows.append(vals)

    if names is None:
        names = [f"系列{i + 1}" for i in range(ncol)] if ncol > 1 else [""]
    names = (names + [""] * ncol)[:ncol]
    return labels, names, rows


def make_fmt(values):
    """1つのグラフ内で小数桁をそろえるフォーマッタを作る。"""
    if all(abs(v - round(v)) < 1e-9 for v in values):
        dec = 0
    else:
        # 倍率(1.19 vs 1.17)のような小さい値は1桁だと潰れるので2桁にする
        dec = 2 if max(abs(v) for v in values) < 10 else 1

    def fmt(v):
        return "-" if v is None else f"{v:,.{dec}f}"

    return fmt


def draw_bar(labels, names, rows, args):
    flat = [v for r in rows for v in r if v is not None]
    if not flat:
        sys.exit("chart.py: 有効な数値がありません")
    fmt = make_fmt(flat)

    lo, hi = min(0.0, min(flat)), max(0.0, max(flat))
    span = (hi - lo) or 1.0
    nser = len(names)

    lab_w = min(args.label_width, max(disp_width(l) for l in labels))
    ser_w = max((disp_width(n) for n in names), default=0) if nser > 1 else 0
    val_w = max(len(fmt(v)) for v in flat)
    area = args.width - lab_w - ser_w - val_w - (5 if nser > 1 else 4)
    if area < 10:
        area = 10
    zero = min(round(-lo / span * area), area - 1) if lo < 0 else 0

    out = []
    if args.title:
        out += [args.title, ""]

    for li, label in enumerate(labels):
        for si in range(nser):
            v = rows[li][si]
            head = pad(clip(label, lab_w), lab_w) if si == 0 else " " * lab_w
            if nser > 1:
                head += " " + pad(clip(names[si], ser_w), ser_w)

            line = [" "] * area
            if lo < 0:
                line[zero] = "│"
            if v is not None:
                length = abs(v) / span * area
                fill = FILLS[si % len(FILLS)]
                if v >= 0:
                    full = int(length)
                    for i in range(min(full, area - zero)):
                        line[zero + i] = fill
                    frac = length - full
                    if frac > 0.06 and zero + full < area:
                        # 端数の細ブロックは█系しかないので、他系列は塗りを揃える
                        line[zero + full] = (BLOCKS[min(8, round(frac * 8))]
                                             if si == 0 else
                                             (fill if frac >= 0.5 else " "))
                else:
                    for i in range(1, min(round(length), zero) + 1):
                        line[zero - i] = fill
            bar = "".join(line).rstrip() or ("│" if lo < 0 else "")
            out.append(f"{head} {pad(bar, area)} {pad(fmt(v), val_w, 'right')}".rstrip())
        if nser > 1 and li != len(labels) - 1:
            out.append("")
    return "\n".join(out)


def draw_line(labels, names, rows, args):
    flat = [v for r in rows for v in r if v is not None]
    if not flat:
        sys.exit("chart.py: 有効な数値がありません")
    if len(rows) < 2:
        return draw_bar(labels, names, rows, args)
    fmt = make_fmt(flat)

    lo, hi = min(flat), max(flat)
    if args.zero:
        lo = min(0.0, lo)
    if hi == lo:
        hi, lo = hi + 1, lo - 1
    pad_v = (hi - lo) * 0.05
    lo, hi = lo - pad_v, hi + pad_v

    h = max(5, args.height)
    axis_w = max(len(fmt(lo)), len(fmt(hi)))
    n = len(rows)
    # 点を詰めすぎると線が潰れ、離しすぎると点線が散らかるので 1点=6桁を目安に
    w = max(20, min(args.width - axis_w - 2, (n - 1) * 6))

    grid = [[" "] * w for _ in range(h)]

    def row_of(v):
        return h - 1 - int(round((v - lo) / (hi - lo) * (h - 1)))

    for si, _ in enumerate(names):
        mark = MARKS[si % len(MARKS)]
        pts = []  # (col, row)
        for i in range(n):
            v = rows[i][si]
            if v is None:
                continue
            pts.append((round(i / (n - 1) * (w - 1)), row_of(v)))
        for k, (c, r) in enumerate(pts):
            if k:  # 直前の点との間を補間して線に見せる
                pc, pr = pts[k - 1]
                for cc in range(pc + 1, c):
                    t = (cc - pc) / (c - pc)
                    rr = round(pr + (r - pr) * t)
                    if grid[rr][cc] == " ":
                        grid[rr][cc] = "·"
            grid[r][c] = mark

    out = []
    if args.title:
        out += [args.title, ""]
    for r in range(h):
        if r == 0:
            tick = fmt(hi)
        elif r == h - 1:
            tick = fmt(lo)
        elif r == h // 2:
            tick = fmt((hi + lo) / 2)
        else:
            tick = ""
        out.append(f"{pad(tick, axis_w, 'right')} │{''.join(grid[r]).rstrip()}")
    out.append(f"{' ' * axis_w} └{'─' * w}")

    # x軸ラベル: 最初・真ん中・最後だけ
    xl = [" "] * w
    for i in (0, n // 2, n - 1):
        c = round(i / (n - 1) * (w - 1))
        s = clip(labels[i], 12)
        start = min(max(0, c - disp_width(s) // 2), w - disp_width(s))
        if all(xl[start + k] == " " for k in range(disp_width(s))):
            for k, ch in enumerate(s):
                xl[start + k] = ch
            for k in range(len(s), disp_width(s)):
                xl[start + k] = ""
    out.append(f"{' ' * axis_w}  {''.join(xl).rstrip()}")

    if len(names) > 1 or names[0]:
        out.append("")
        out.append("  ".join(f"{MARKS[i % len(MARKS)]} {nm}"
                             for i, nm in enumerate(names) if nm))
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("kind", choices=["bar", "line"])
    p.add_argument("file", nargs="?", help="省略時は標準入力")
    p.add_argument("--title", "-t", default="")
    p.add_argument("--width", "-w", type=int, default=72, help="全体の幅 (既定72)")
    p.add_argument("--height", type=int, default=12, help="lineの高さ (既定12)")
    p.add_argument("--label-width", type=int, default=20, help="ラベル欄の最大幅")
    p.add_argument("--sort", choices=["asc", "desc"], help="第1系列で並べ替え")
    p.add_argument("--zero", action="store_true", help="lineでもy軸に0を含める")
    args = p.parse_args()

    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    labels, names, rows = parse(text)

    if args.sort:
        have = [i for i in range(len(rows)) if rows[i][0] is not None]
        have.sort(key=lambda i: rows[i][0], reverse=(args.sort == "desc"))
        order = have + [i for i in range(len(rows)) if rows[i][0] is None]
        labels = [labels[i] for i in order]
        rows = [rows[i] for i in order]

    draw = draw_bar if args.kind == "bar" else draw_line
    print(draw(labels, names, rows, args))


if __name__ == "__main__":
    main()
