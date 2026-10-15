---
name: spreadsheet
description: "CSVのデータからGoogleスプレッドシートを作る。rawシート＋そこを参照する生きた数式（QUERY等）の構成を、xlsx組み立て→Driveアップロードで実現する。TRIGGER: 「スプレッドシート作って」「スプシに集計を」「CSVをスプシに」「シートにまとめて」等。"
---

# spreadsheet — CSV から Google スプレッドシートを作る

raw データのシートと、**そこを参照する生きた数式**の集計シートを持つスプレッドシートを作る。
同僚が開いて編集・組み替えできる状態で共有することが目的。

## 大前提：ベタ貼りは禁止

pandas で計算した結果を値として貼るのは**明確に拒否されている**。
集計は必ず **シート上の数式** で組み、raw シートが変われば追従する状態にすること。
Python の役割は「シートを組み立てる」ことだけで、計算はシート上で走らせる。

## なぜこの方法なのか

GCP プロジェクトが使えないため、gspread / Sheets API 直叩きは選択肢に無い。
代わりに **openpyxl で xlsx を組み立て → Google Drive 連携でアップロード**（Google スプレッドシートに自動変換）する。

検証済み（2026-07-28）：xlsx に書いた数式は変換後も**生きた数式**として残る。
Excel に存在しない Google 独自関数 `QUERY` / `FILTER` も評価される。日本語のデータもラベルも問題ない。

## 手順

### 1. spec JSON を書く

```json
{
  "out": "<scratchpad>/out.xlsx",
  "sheets": [
    {"name": "raw", "csv": "/path/to/data.csv"},
    {"name": "shukei", "cells": {
      "A1": "カテゴリ別集計",
      "A2": "=QUERY(raw!A:C, \"select A, sum(C) where A is not null group by A label sum(C) '合計'\", 1)"
    }}
  ]
}
```

- `csv` … その CSV を値として流し込む（数値は数値型に変換される）
- `cells` … A1 形式のセル指定。`=` 始まりは数式として入る
- `encoding` … 省略可。CSV が cp932 のときなどに指定

### 2. ビルド

```bash
python ~/.claude/skills/spreadsheet/scripts/build_xlsx.py spec.json
```

xlsx と、同じ場所に `.b64`（base64）が出る。

### 3. アップロード

`.b64` の中身を読んで、Google Drive の `create_file` に渡す。

- `contentMimeType`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `base64Content`: `.b64` の中身
- `title`: 適当な名前

**mimeType を間違えると Google スプレッドシートに変換されない。** ここが一番の落とし穴。

#### `Request contains an invalid argument` が出たとき

**ウィンドウ枠の固定（`freeze_panes`）を疑うこと。** openpyxl が書く `<pane>` 要素が
入っていると、Drive のアップロードがこのエラーで必ず失敗する（2026-07-28 に切り分け済み。
`<pane>` の有無だけが違う2ファイルで、有りは失敗・無しは成功）。
`build_xlsx.py` は `freeze` をサポートしていないので、自前で `ws.freeze_panes` を
足したりしないこと。枠の固定が要るなら UI 側でやってもらう。

サイズは原因ではない（7,404 文字の base64 でも `<pane>` があれば失敗した）。

### 4. 検証

`read_file_content` で読み返し、**数式が評価された結果が入っているか**を確認する。
`QUERY` / `FILTER` は Excel に無い関数なので、openpyxl は計算済み値を一切書いていない。
それでも結果が出ていれば、Google 側が数式として解釈した証拠になる。

`#NAME?` や空欄が出ていたら数式が壊れている。

最後に URL をユーザーに渡す。

## 数式のコツ

- **`QUERY` が主力。** `=QUERY(raw!A:C, "select A, sum(C) where A is not null group by A label sum(C) '合計'", 1)`
  - 末尾の `1` はヘッダ行数
  - `label` を付けないと列名が `sum 金額` のようになる
  - `where A is not null` を入れると末尾の空行を拾わない
- **クロス集計は `QUERY` の `pivot` 句で作れる。** `=QUERY(raw!A:E, "select A, sum(D) where A is not null group by A pivot B", 1)`
  で「行=カテゴリ、列=月」の表になる。ネイティブのピボットテーブルは作れないが、
  見た目の集計表としてはこれでほぼ代替できる（検証済み）
- **`FILTER` / `QUERY` は下方向にも右方向にも配列展開する。** 結果の行数・列数ぶん余白を空けておくこと。詰めて置くと `#REF!` になる。
  `pivot` は列数が事前に読めないので特に広めに空ける
- **シート名は英数字推奨。** 日本語シートを参照するなら `='集計'!A1` のようにシングルクォートで囲む（日本語シート名からの参照は未検証）
- 列全体参照（`raw!A:C`）にしておくと、あとで raw の行数が増えても数式を直さずに済む

## 制約（作る前にユーザーに伝えること）

1. **ネイティブのピボットテーブルは作れない**
   openpyxl / xlsxwriter とも新規作成に非対応。UI でドラッグして組み替えるあの機能が要るなら、
   スプレッドシート上で1回だけ手作業で作ってもらう。`QUERY` で同等の集計表は出せる。

2. **既存シートの更新はできず、毎回新規ファイルになる**
   同じ URL を保ちたい場合は、Google Sheets 側で
   **ファイル > インポート > アップロード > 「現在のシートを置き換える」** を案内する。
   これなら URL も集計シートの数式もそのまま残り、raw の中身だけ差し替わる。

3. **サイズ上限がある**
   base64 を出力に載せる必要があるので、大きいファイルは context を圧迫する。
   目安は**数千行まで**。`build_xlsx.py` が警告を出したら、xlsx を手動で Drive に
   アップロードしてもらう（xlsx の中身は同じなので数式は同様に生きる）。
