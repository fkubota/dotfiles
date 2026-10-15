#!/usr/bin/env python3
"""JSON spec から xlsx を組み立てて base64 まで吐く。

usage:
    python build_xlsx.py spec.json

spec の形:
{
  "out": "/path/to/out.xlsx",
  "sheets": [
    {"name": "raw", "csv": "/path/to/data.csv", "encoding": "utf-8", "freeze": "A2"},
    {"name": "shukei", "cells": {"A1": "=QUERY(raw!A:C, \"select A, sum(C) group by A\", 1)"}}
  ]
}

- csv:    その CSV を値としてシートに流し込む（数値は数値型に変換）
- cells:  A1 形式のセル指定。"=" 始まりは数式として入る

ウィンドウ枠の固定（freeze_panes）はサポートしない。
openpyxl が書く <pane> 要素が入っていると Drive のアップロードが
"Request contains an invalid argument" で失敗する（2026-07-28 検証済み）。
固定したい場合はスプレッドシートの UI 側でやってもらうこと。
"""

import base64
import csv
import json
import sys
from pathlib import Path

from openpyxl import Workbook

# base64 がこの長さを超えると MCP 経由のアップロードで context を圧迫する
B64_WARN_CHARS = 100_000


def to_cell_value(s):
    """CSV の文字列を、可能なら数値に変換する。

    先頭ゼロ（"007"）や指数表記に化けそうなものは文字列のまま残す。
    """
    if s == "":
        return None
    if s.lstrip("-").startswith("0") and s.strip("-") not in ("0",) and "." not in s:
        return s
    for cast in (int, float):
        try:
            return cast(s)
        except ValueError:
            pass
    return s


def add_csv_sheet(ws, csv_path, encoding="utf-8"):
    with open(csv_path, newline="", encoding=encoding) as f:
        for row in csv.reader(f):
            ws.append([to_cell_value(c) for c in row])


def add_cells(ws, cells):
    for ref, value in cells.items():
        ws[ref] = value


def build(spec):
    wb = Workbook()
    wb.remove(wb.active)

    for sheet in spec["sheets"]:
        ws = wb.create_sheet(sheet["name"])
        if "csv" in sheet:
            add_csv_sheet(ws, sheet["csv"], sheet.get("encoding", "utf-8"))
        if "cells" in sheet:
            add_cells(ws, sheet["cells"])

    out = Path(spec["out"])
    wb.save(out)
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = build(spec)

    data = out.read_bytes()
    b64 = base64.b64encode(data).decode()
    b64_path = out.with_suffix(".b64")
    b64_path.write_text(b64)

    print(f"xlsx : {out} ({len(data):,} bytes)")
    print(f"base64: {b64_path} ({len(b64):,} chars)")
    if len(b64) > B64_WARN_CHARS:
        print(
            f"\n[warn] base64 が {B64_WARN_CHARS:,} 文字を超えている。"
            "MCP でのアップロードは context を圧迫するので、"
            "xlsx を手動で Drive にアップロードすること。"
        )


if __name__ == "__main__":
    main()
