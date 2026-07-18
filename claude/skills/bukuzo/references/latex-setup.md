# LaTeX 設定の詳細（main.tex 雛形・図ツールのセットアップ）

新規プロジェクト作成時（main.tex 雛形の作成）、および図ツールの初期設定時に参照する。

## 推奨 LaTeX 設定（main.tex 雛形）

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

## 部・章・節・項の階層（ltjsbook）

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

## tcolorbox スタイル（3種推奨）

| スタイル名 | 用途 | 枠色 |
|---|---|---|
| `pointbox` | ポイント・まとめ | primaryColor（コーラルなど） |
| `warningbox` | 注意・禁止事項 | 濃赤 |
| `termbox` | 用語定義 | グリーン |

## TikZ（フロー図・概念図）のセットアップ

LaTeX ネイティブのため追加ツール不要。ベクター品質でそのまま PDF に埋め込まれる。
`main.tex` のプリアンブルに以下を追加する:

```latex
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, fit, calc}
```

## graphviz（DAG・依存関係図）のセットアップ

```bash
# インストール（初回のみ）
brew install graphviz

# PNG 生成
dot -Tpng scripts/fig_xxx.dot -o figures/fig_xxx.png
```

dot ファイルは `scripts/` に置き、生成した PNG を `figures/` に出力する。
Makefile の `figures:` ターゲットに追加しておくこと。
