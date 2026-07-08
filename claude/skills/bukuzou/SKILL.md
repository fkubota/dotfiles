---
name: bukuzou
description: LuaLaTeX + Python matplotlib で技術書・社内教科書を作成・編集する
disable-model-invocation: true
---

# bukuzou

LuaLaTeX（MacTeX）と Python matplotlib を使って、技術書・社内教科書を作成・編集するスキルです。
複数のソース（ナレッジベース、コードベース、外部ドキュメント）から内容を収集し、PDF にまとめます。

---

## 引数による振る舞い

| 呼び出し形式 | 動作 |
|---|---|
| `/bukuzou` (引数なし) | AskUserQuestion で「新規作成 / 既存を開く / キャンセル」を提示 |
| `/bukuzou new` | 新規作成フローを直接開始 |
| `/bukuzou <キーワード>` | キーワードで既存プロジェクトを検索し選択 |
| 書籍プロジェクトディレクトリ内で実行 | 自動的に再開フロー |

書籍プロジェクトディレクトリの判定: カレントディレクトリ（またはその親）に `.book/LOG.md` が存在する場合。

---

## 書籍の階層構造

ltjsbook では以下の4階層を使う:

| LaTeX コマンド | 日本語呼称 | 番号例 |
|---|---|---|
| `\part{...}` | 部 | 第1部、第2部 |
| `\chapter{...}` | 章 | 第1章、第2章 |
| `\section{...}` | 節 | 1.1、1.2 |
| `\subsection{...}` | 項 | 1.1.1、1.1.2 |

- 部は大きなテーマのまとまり（3〜5章を束ねる）
- 章が本文の基本単位（1ファイル = 1章）
- 節・項は章内の見出し（.tex ファイルは分割しない）
- 付録は `\appendix` 以降に `\chapter` として配置

---

## プロジェクト構造

書籍プロジェクトの作業ディレクトリは以下の構成とする:

```
<workdir>/
├── main.tex              # マスターLaTeXファイル（\part・\chapter の \input を列挙）
├── chapters/             # 章ごとの .tex ファイル（1ファイル = 1章）
│   ├── p1_ch01_xxx.tex   # 第1部 第1章
│   ├── p1_ch02_xxx.tex   # 第1部 第2章
│   ├── p2_ch03_xxx.tex   # 第2部 第3章
│   └── appendix_a.tex    # 付録A（用語集など）
├── figures/              # 生成済み PNG 図
├── scripts/              # Python matplotlib スクリプト
│   └── fig_xxx.py
└── .book/                # プロジェクト管理ファイル（必須）
    ├── SUMMARY.md        # 書籍概要（ユーザーが参照）
    ├── RULES.md          # 編集ルール・用語統一表・スタイル設定
    ├── TODO.md           # 作業タスク
    └── LOG.md            # セッション間の引き継ぎログ（Claude 用）
```

### main.tex での部・章の組み方

```latex
\part{人件費管理の課題とHANZO}
\input{chapters/p1_ch01_xxx}
\input{chapters/p1_ch02_xxx}

\part{主要機能詳解}
\input{chapters/p2_ch03_xxx}

\appendix
\input{chapters/appendix_a}
```

---

## `.book/` ファイルの役割

### SUMMARY.md
- 書籍タイトル・読者対象・目的
- 現在の章構成と各章の概要
- ページ数・コンパイル状態

### RULES.md
編集ルールを集約するファイル。ユーザーが「〇〇してほしい」と指示したルールをここに追記していく。

- **編集ルール**: 章を書き終えた後に行うチェック内容（例: 「用語集との不整合確認」「tcolorbox の使用頻度を均一に」など）
- **用語統一表（ユビキタス言語）**: 概念と対応する術語の一覧（表記ゆれを防ぐ）
- **カラーテーマ**: 使用色のHEXコードと用途
- **数式記号表**: 記号・意味・単位の対応
- **LaTeX設定**: ドキュメントクラス・パッケージ・tcolorboxスタイル
- **図スタイル**: matplotlib のフォント・色・サイズ設定

> ルールはユーザーの指示があったタイミングで追記する。セッション開始時に読み込み、執筆中は常に参照する。

### TODO.md
- 残り章・残り図・残り品質チェック項目

### LOG.md
- 別セッションで再開できるよう、直近の作業状況・決定事項・次のアクションを記録
- 新セッション開始時にこのファイルを読んで状況を把握する

---

## 新規作成フロー

1. **タイトルを質問**: 「書籍のタイトルを教えてください」
2. **作業ディレクトリを確認**: AskUserQuestion で選択
   - 「既存のパスを指定する」→ パスを入力してもらう
   - 「新しく作る」→ `~/work/google_drive/bukuzou/<タイトル>/` を提案
3. **読者対象を質問**: 社内向け / カスタマー向け / 外部公開 など
4. **用語集と編集ルールを確認**:
   - 「用語集（巻末付録）を作成し、本文から双方向リンクを入れますか？」を AskUserQuestion で確認
   - ユーザーが「〇〇してほしい」と言った編集ルールがあれば RULES.md に記録
5. **カラーテーマを確認**: ブランドカラーの HEX コードまたは「デフォルト」
6. **出力 PDF ファイル名を確認**: AskUserQuestion で質問する
   - デフォルト: `<書籍タイトル>.pdf`
   - ユーザーが別名を指定した場合はそれを使用
   - main.tex の `\jobname` ではなく、コンパイル時に `-jobname` オプションで指定する:
     ```bash
     lualatex -jobname="出力ファイル名（拡張子なし）" main.tex
     ```
   - SUMMARY.md と LOG.md に出力ファイル名を記録する
7. **ソースを確認**: 以下から複数選択（AskUserQuestion, multiSelect: true）
   - ナレッジベース（Markdown ファイル群）
   - コードベース（ディレクトリパス）
   - 外部 URL
   - ユーザーが直接テキストを提供
8. **部・章構成を提案**: ソースを読んで「部 → 章」の目次案を提示 → 合意を得る
   - 部（\part）は大きなテーマのまとまり
   - 章（\chapter）が本文の基本単位
   - ファイル名は `p{部番号}_ch{章番号}_{英名}.tex` 形式
9. **プロジェクトディレクトリ・`.book/` ファイルを作成**
10. **main.tex の雛形を作成**: ltjsbook クラス、\part/\chapter 構造、カラー定義、tcolorbox スタイル込み
11. 執筆開始

---

## 再開フロー

1. `.book/LOG.md`, `.book/SUMMARY.md`, `.book/TODO.md`, `.book/RULES.md` を読み込む
2. 「前回は〇〇章まで完成、残りは〇〇」と状況を表示
3. 次のアクションを提案（次章の執筆 / 品質チェック / 特定章の修正 など）

---

## 既存プロジェクト検索フロー

1. `ls ~/work/google_drive/bukuzou/` を実行
2. `.book/LOG.md` が存在するディレクトリを書籍プロジェクトとして抽出
3. 各プロジェクトの `.book/SUMMARY.md` の1行目（タイトル）も取得
4. キーワードで部分一致フィルタリング
5. 上位5件を AskUserQuestion で選択（multiSelect: false）

---

## ビルドシステム

### PDF コンパイル

```bash
export PATH="/Library/TeX/texbin:$PATH"
# 出力ファイル名を指定する場合（デフォルト: 書籍タイトル.pdf）
lualatex -interaction=nonstopmode -jobname="出力ファイル名（拡張子なし）" main.tex
lualatex -interaction=nonstopmode -jobname="出力ファイル名（拡張子なし）" main.tex  # 参照解決のため2回実行
```

- 作業ディレクトリで実行すること（`figures/` への相対パスのため）
- `-jobname` を省略すると `main.pdf` が生成される（書籍タイトルにしたい場合は必ず指定）
- エラーが出た場合は `main.log` を確認する

### 図の種類と使い分け

図の内容によってツールを使い分ける。

| 図の種類 | ツール | 記法 |
|---|---|---|
| データ可視化（折れ線・散布図・棒グラフ） | **matplotlib**（Python） | `scripts/fig_xxx.py` → `figures/fig_xxx.png` |
| フロー図・概念図・タイムライン（箱と矢印） | **TikZ**（LaTeX ネイティブ） | `.tex` ファイル内に直接記述 |
| シンプルな DAG・依存関係図 | **graphviz（dot）** | `scripts/fig_xxx.dot` → `figures/fig_xxx.png` |

#### TikZ（フロー図・概念図）

LaTeX ネイティブのため追加ツール不要。ベクター品質でそのまま PDF に埋め込まれる。
`main.tex` のプリアンブルに以下を追加する:

```latex
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, fit, calc}
```

#### graphviz（DAG・依存関係図）

```bash
# インストール（初回のみ）
brew install graphviz

# PNG 生成
dot -Tpng scripts/fig_xxx.dot -o figures/fig_xxx.png
```

dot ファイルは `scripts/` に置き、生成した PNG を `figures/` に出力する。
Makefile の `figures:` ターゲットに追加しておくこと。

### 図の生成

```bash
python scripts/fig_xxx.py
```

- 全 `scripts/fig_*.py` を LaTeX コンパイル前に実行する
- 出力先は `figures/` に統一する
- フォント: macOS では `Hiragino Sans`（日本語対応）

### 図のビジュアルチェック（必須）

図を新規作成・更新したあと、またはコンパイル後に、**全ての図**を目視確認する。

```bash
# figures/ 内の全 PNG を確認する
ls figures/*.png
```

Read ツールで各 PNG ファイルを開き、以下の項目をチェックする:

| チェック項目 | 確認内容 |
|---|---|
| 凡例（legend）の重なり | 凡例がデータ・軸ラベル・タイトルと重なっていないか |
| 矢印のずれ | 矢印の始点・終点がボックスやノードから外れていないか |
| **矢印とデータ線の整合** | `ax.annotate` の arrowhead が折れ線の対応する点に乗っているか。matplotlib ループで「発注追加 → annotate → 消費 → append」の順だと arrowhead が消費分だけ浮く（ズレバグ）。消費・append の後に annotate するか、フラグで遅延させること |
| テキストの切れ | ラベル・タイトル・軸の文字が枠外にはみ出していないか |
| フォントの文字化け | 日本語が豆腐（□）になっていないか |
| 余白の過不足 | 上下左右に極端な空白・はみ出しがないか |
| 色の視認性 | 似た色が隣り合って区別しにくくなっていないか |

問題が見つかった場合はスクリプト（または TikZ コード）を修正して再生成し、再度チェックする。
全図の確認が完了するまでコンパイル報告をしない。

### 推奨 LaTeX 設定（main.tex 雛形）

```latex
\documentclass[12pt,a4paper,openany]{ltjsbook}
\usepackage{luatexja}
\usepackage{luatexja-fontspec}
\usepackage[top=25mm,bottom=25mm,left=28mm,right=28mm,footskip=12mm]{geometry}
\usepackage{graphicx}
\usepackage[dvipsnames,svgnames,x11names]{xcolor}
\usepackage[most,breakable]{tcolorbox}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{enumitem}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage[unicode,colorlinks=true,linkcolor=primaryColor,urlcolor=primaryColor]{hyperref}
```

### 部・章・節・項の階層（ltjsbook）

```latex
\part{第1部 タイトル}    % 部：大テーマのまとまり
  \chapter{タイトル}     % 章：1ファイル = 1章
    \section{タイトル}   % 節：章内の大見出し
      \subsection{タイトル}  % 項：節内の小見出し
```

**重要**: `\section` や `\subsection` のタイトルに「3.2」「3.4.1」などの番号を書いてはいけない。
LaTeX が自動で番号を付けるため、書くと「3.4.1　3.4.1 仕組み」のように二重表示になる。

- 節番号は `章番号.節番号` で自動生成（例: 3.2）
- 項番号は `章番号.節番号.項番号` で自動生成（例: 3.2.1）
- `\setcounter{tocdepth}{2}` で目次に節まで表示（項は非表示）
- `\setcounter{secnumdepth}{3}` で項まで番号付け

### tcolorbox スタイル（3種推奨）

| スタイル名 | 用途 | 枠色 |
|---|---|---|
| `pointbox` | ポイント・まとめ | primaryColor（コーラルなど） |
| `warningbox` | 注意・禁止事項 | 濃赤 |
| `termbox` | 用語定義 | グリーン |

---

## 用語集とページ参照

### 仕組み

章内で新用語を定義するとき:
```latex
\phantomsection\label{term:用語名}
```

用語集（appendix_a.tex）でページ参照:
```latex
\pageref{term:用語名} ページ参照
```

### 品質チェック（章追加後に自動実行）

新しい章を書き終えたタイミングで以下を自動チェックする:

1. **`\pageref` カバレッジ**: 用語集の全エントリに対応する `\label` が存在するか確認
2. **新用語の追加**: 章内の新概念が用語集（appendix_a.tex）に追加されているか確認
3. **コンパイル確認**: `Undefined references` が 0 であることを確認

---

## ユビキタス言語レビュー（全章執筆完了後に実行）

全章の執筆が一通り完了した後に行う用語統一フロー。
用語集（appendix_a.tex）を正（source of truth）として本文全体の表記を統一する。

### フロー

#### ステップ1: 用語集の全エントリを抽出
`appendix_a.tex` の `\item[用語名]` をすべて読み出し、**正式用語リスト**を作成する。

#### ステップ2: 全章を横断して用語の使われ方を収集

各章ファイルに対して以下を調べる:
- 正式用語リストの用語と**微妙に異なる表記**（例: 「人件費率」vs「人時売上高」、「配置基準」vs「配置モデル」）
- **同じ概念を複数の単語で表現**しているケース（用語集に登録されていない揺れ）

収集結果を以下の2種に分類する:

| 分類 | 内容 | 対応 |
|---|---|---|
| **A: 用語集との表記ゆれ** | 用語集に登録済みの概念が、本文で別の書き方をされている | 用語集の表記に自動修正 |
| **B: 未登録の表記ゆれ** | 用語集にない概念が複数の単語で表現されている | ユーザーに相談して決定 |

#### ステップ3: A（用語集との表記ゆれ）を自動修正

用語集の表記を正として、該当箇所を自動的に置換する。
修正後に対象ファイルを保存する。

#### ステップ4: B（未登録の表記ゆれ）をユーザーに相談

以下の形式で報告し、どれを正式用語にするか確認する:

```
【表記ゆれ】「〇〇」「△△」「□□」が同じ概念を指しています。
- ソースコード: `xxxxx`（英名: xxx）
- HANZO-DOCS:「△△」が多用されています
→ サジェスト: 「△△」を正式用語にすることを推奨します。いかがでしょうか？
```

ユーザーが選択したら:
1. 用語集（appendix_a.tex）に正式用語として追加する
2. `RULES.md` の用語統一表に追記する
3. 全章の本文を正式用語に統一する

#### ステップ5: コンパイルして最終確認

```bash
lualatex -interaction=nonstopmode -jobname="出力ファイル名" main.tex
lualatex -interaction=nonstopmode -jobname="出力ファイル名" main.tex
```

Undefined references = 0 を確認する。

### サジェストの根拠

B の未登録表記ゆれをサジェストする際は、以下の優先順位でソースを参照する:

1. **ソースコード**（モデル名・カラム名・クラス名などの英語識別子から日本語名を推定）
2. **HANZO-DOCS**（ドメイン仕様書・要件定義書での使用頻度）
3. **用語集の既存エントリ**（類似概念との整合性）

根拠を明示したうえでサジェストし、最終決定はユーザーに委ねる。

---

## 複数ソースの扱い方

| ソース種別 | 取得方法 | 使い方 |
|---|---|---|
| Markdown ナレッジファイル | Read ツールで直接読む | 内容をまとめて章原稿に変換 |
| コードベース | Bash/Grep でシンボル・コメントを収集 | 実装の説明・図の元データに使用 |
| 外部 URL | WebFetch で取得 | 概念説明・参考資料として引用 |
| ユーザーのテキスト | 会話から直接取得 | そのまま章原稿として整形 |

ソースが多い場合は、章単位でソースを割り当て、エージェントで並列処理することを推奨。

---

## セッション終了時

ユーザーが「終わり」「今日はここまで」などと言った場合:
1. `.book/LOG.md` を更新（作業状況・次のアクション）
2. `.book/TODO.md` を更新（完了タスクにチェック、残タスクを整理）
3. `.book/SUMMARY.md` を更新（ページ数・章構成の現在状態）
4. 「次回は〇〇から再開できます」と伝える

---

## イントロ表示

コマンド開始時に以下を実行する:

```bash
printf "\n\033[1;93m╔════════════════════════════════════════════════╗\033[0m\n"
printf "\033[1;93m║              \033[1;92m📖 BUKUZOU \033[1;95mACTIVATED\033[1;93m              ║\033[0m\n"
printf "\033[1;93m╚════════════════════════════════════════════════╝\033[0m\n\n"
```

---

## 実行開始

引数（`$ARGUMENTS`）と現在のディレクトリを確認し、上記のルールに従って動作してください。
